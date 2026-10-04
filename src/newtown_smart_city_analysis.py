# %% [markdown]
# # Smart Cities and Urban Analytics Using Spatial Data — New Town Kolkata
#
# **GIS term project, IIT Kharagpur.** This notebook runs the whole analysis end to end with ready-made open data:
#
# | Module | What it does | Data |
# | --- | --- | --- |
# | A | Land cover classification (Random Forest) and built-up growth | Sentinel-2 + Dynamic World labels |
# | B | Land surface temperature and surface urban heat island | Landsat 8/9 Collection 2 Level-2 |
# | C | 15-minute walking accessibility to five services | OpenStreetMap (OSMnx) + WorldPop |
# | D | Smart Liveability Index (AHP) and spatial clustering | Outputs of A–C |
#
# **How to run (about 15–25 minutes):**
# 1. Open in Google Colab. Register a free Earth Engine Cloud project at https://code.earthengine.google.com/register (non-commercial / academic) and paste its ID into `PROJECT_ID` below.
# 2. *Optional:* upload a boundary GeoJSON of the NKDA area and set `BOUNDARY_FILE`. Otherwise the notebook tries OSM, then falls back to a bounding box.
# 3. Runtime → Run all. Everything is written to `outputs/` (figures, tables, `results.md`) and zipped at the end.

# %%
# %pip install -q osmnx geemap libpysal esda statsmodels rasterio

# %% [markdown]
# ## 0. Configuration

# %%
PROJECT_ID = "newton-gis2"   # <-- change this

YEARS = [2016, 2021, 2026]          # dry-season year label: Nov (year-1) to Feb (year)
BOUNDARY_FILE = None                # e.g. "newtown_boundary.geojson"
ACTION_AREAS_FILE = None            # optional GeoJSON with a 'name' column (Action Areas I, II, III)
PLACE_QUERY = "New Town, North 24 Parganas, West Bengal, India"
FALLBACK_BBOX = (88.430, 22.555, 88.510, 22.640)   # lon_min, lat_min, lon_max, lat_max

CRS = "EPSG:32645"        # WGS 84 / UTM zone 45N, metres
HEX_WIDTH = 250           # flat-to-flat hexagon width, m
BUFFER_M = 2000           # buffer for edge effects and rural LST reference
DW_CONF = 0.6             # min Dynamic World probability for a training pixel
SAMPLES_PER_CLASS = 400   # stratified training + validation points per class
WALK_SPEED_KMH = 4.8
WALK_MINUTES = 15
OUT = "outputs"

CLASS_NAMES = ["Water / wetland", "Vegetation", "Cropland", "Built-up", "Bare / fallow"]
CLASS_COLORS = ["#2b7bba", "#3a9a48", "#d8c35a", "#d7301f", "#b39d7a"]

# Five SLI indicators: (column, lower-is-better?)
SLI_SPEC = [("NDVI", False), ("LST", True), ("f_bluegreen", False), ("score15", False), ("d_transit_cap", True)]
SLI_LABELS = ["Green cover", "Thermal comfort", "Blue-green share", "15-minute accessibility", "Transit proximity"]
# AHP pairwise matrix (Saaty 1–9), rows/cols in SLI_SPEC order. Edit to reflect your group's judgement.
AHP_MATRIX = [
    [1,   1,   2,   1/3, 1/2],
    [1,   1,   2,   1/3, 1/2],
    [1/2, 1/2, 1,   1/4, 1/3],
    [3,   3,   4,   1,   2  ],
    [2,   2,   3,   1/2, 1  ],
]

SERVICES = {
    "school":  {"amenity": ["school", "college"]},
    "health":  {"amenity": ["hospital", "clinic", "doctors", "pharmacy"]},
    "green":   {"leisure": ["park", "garden", "playground"]},
    "transit": {"highway": ["bus_stop"], "railway": ["station", "halt", "subway_entrance"]},
    "shop":    {"shop": ["supermarket", "convenience", "greengrocer"], "amenity": ["marketplace"]},
}
SERVICE_LABELS = {"school": "School", "health": "Health", "green": "Park / green space",
                  "transit": "Public transit", "shop": "Daily shopping"}

# %% [markdown]
# ## 1. Imports and helper functions

# %%
import copy, json, os, shutil, warnings
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
from shapely.geometry import Point, Polygon, box
from shapely.prepared import prep
from scipy import stats
import statsmodels.api as sm
from libpysal.weights import Queen, KNN
from esda.moran import Moran, Moran_Local
from esda.getisord import G_Local

warnings.filterwarnings("ignore")
for sub in ("figures", "tables", "data"):
    os.makedirs(f"{OUT}/{sub}", exist_ok=True)


def make_hex_grid(boundary_proj, width=250.0):
    """Pointy-top hexagons (flat-to-flat = width) whose centroids fall inside the boundary."""
    a = width / np.sqrt(3)
    dy = 1.5 * a
    poly = boundary_proj.geometry.union_all() if hasattr(boundary_proj.geometry, "union_all") \
        else boundary_proj.geometry.unary_union
    inside = prep(poly)
    minx, miny, maxx, maxy = poly.bounds
    ang = np.deg2rad(np.arange(30, 390, 60))
    cells, row, y = [], 0, miny - a
    while y <= maxy + a:
        x = minx - width + (width / 2 if row % 2 else 0)
        while x <= maxx + width:
            if inside.contains(Point(x, y)):
                cells.append(Polygon(zip(x + a * np.cos(ang), y + a * np.sin(ang))))
            x += width
        y += dy
        row += 1
    return gpd.GeoDataFrame({"hex_id": [f"h{i:04d}" for i in range(len(cells))]},
                            geometry=cells, crs=boundary_proj.crs)


RANDOM_INDEX = {1: 0, 2: 0, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45}


def ahp_weights(A):
    A = np.asarray(A, float)
    n = A.shape[0]
    vals, vecs = np.linalg.eig(A)
    k = int(np.argmax(vals.real))
    w = np.abs(vecs[:, k].real)
    w = w / w.sum()
    ci = (vals[k].real - n) / (n - 1)
    cr = ci / RANDOM_INDEX[n] if RANDOM_INDEX[n] else 0.0
    return w, cr


def minmax(s, reverse=False):
    s = pd.Series(s, dtype=float)
    rng = s.max() - s.min()
    x = (s - s.min()) / rng if rng > 0 else s * 0 + 0.5
    return (1 - x if reverse else x).to_numpy()


def compute_sli(df, spec, weights):
    X = np.column_stack([minmax(df[c], rev) for c, rev in spec])
    return X @ np.asarray(weights, float)


def quintiles(v):
    return pd.qcut(pd.Series(v).rank(method="first"), 5, labels=False).to_numpy()


def sensitivity(df, spec, w, delta=0.2):
    base = compute_sli(df, spec, w)
    qb = quintiles(base)
    variants = {"Equal weights": np.ones(len(w)) / len(w)}
    for i, label in enumerate(SLI_LABELS):
        for sign in (1, -1):
            v = np.array(w, float).copy()
            v[i] *= 1 + sign * delta
            variants[f"{label} {'+' if sign > 0 else '-'}{int(delta * 100)}%"] = v / v.sum()
    rows = []
    for name, v in variants.items():
        s = compute_sli(df, spec, v)
        rows.append({"Variant": name,
                     "Spearman rho vs baseline": stats.spearmanr(base, s).correlation,
                     "Hexes changing quintile": int((quintiles(s) != qb).sum())})
    return pd.DataFrame(rows)


def bh_fdr(p, alpha=0.05):
    """Benjamini–Hochberg: boolean array of discoveries."""
    p = np.asarray(p, float)
    n = len(p)
    order = np.argsort(p)
    passed = p[order] <= alpha * np.arange(1, n + 1) / n
    sig = np.zeros(n, bool)
    if passed.any():
        sig[order[: np.max(np.where(passed)[0]) + 1]] = True
    return sig


def build_weights(g):
    w = Queen.from_dataframe(g, use_index=False)
    if w.islands:
        print(f"  {len(w.islands)} island hexes -> using 6-nearest-neighbour weights instead")
        w = KNN.from_dataframe(g, k=6)
    w.transform = "r"
    return w


LISA_NAMES = {1: "High-High", 2: "Low-High", 3: "Low-Low", 4: "High-Low"}


def cluster_stats(g, col, w, seed=42):
    y = g[col].to_numpy(float)
    np.random.seed(seed)
    mi = Moran(y, w, permutations=999)
    lisa = Moran_Local(y, copy.deepcopy(w), permutations=9999)
    sig = bh_fdr(lisa.p_sim)
    lisa_lab = np.where(sig, pd.Series(lisa.q).map(LISA_NAMES).to_numpy(), "Not significant")
    gi = G_Local(y, copy.deepcopy(w), transform="B", permutations=9999, star=True)
    gsig = bh_fdr(gi.p_sim)
    hot = np.where(gsig & (gi.Zs > 0), "Hot spot", np.where(gsig & (gi.Zs < 0), "Cold spot", "Not significant"))
    summary = {"Variable": col, "Global Moran's I": mi.I, "Pseudo p-value": mi.p_sim,
               "High-High hexes": int((lisa_lab == "High-High").sum()),
               "Low-Low hexes": int((lisa_lab == "Low-Low").sum())}
    return summary, lisa_lab, hot


def hex_map(g, col, title, path, boundary=None, cmap="viridis", legend_label=None, categories=None):
    fig, ax = plt.subplots(figsize=(7, 7))
    if categories:
        for cat, color in categories.items():
            sub = g[g[col] == cat]
            if len(sub):
                sub.plot(ax=ax, color=color, edgecolor="white", linewidth=0.2)
        ax.legend(handles=[Patch(color=c, label=k) for k, c in categories.items()],
                  loc="lower left", fontsize=8, frameon=True)
    else:
        g.plot(column=col, ax=ax, cmap=cmap, edgecolor="white", linewidth=0.2, legend=True,
               legend_kwds={"label": legend_label or col, "shrink": 0.6}, missing_kwds={"color": "#dddddd"})
    if boundary is not None:
        boundary.boundary.plot(ax=ax, color="black", linewidth=0.8)
    ax.set_title(title, fontsize=11)
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def md_table(df, floatfmt=2):
    df = df.copy()
    for c in df.columns:
        if pd.api.types.is_float_dtype(df[c]):
            df[c] = df[c].map(lambda v: "" if pd.isna(v) else f"{v:,.{floatfmt}f}")
    cols = [str(c) for c in df.columns]
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
    lines += ["| " + " | ".join(str(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join(lines)


# %% [markdown]
# ## 2. Study area and hexagonal grid

# %%
import osmnx as ox
import networkx as nx

ox.settings.use_cache = True
ox.settings.log_console = False


def load_boundary():
    if BOUNDARY_FILE:
        return gpd.read_file(BOUNDARY_FILE).to_crs(4326)[["geometry"]].dissolve(), f"user file ({BOUNDARY_FILE})"
    try:
        g = ox.geocode_to_gdf(PLACE_QUERY)
        area = g.to_crs(CRS).area.iloc[0] / 1e6
        if g.geom_type.iloc[0] in ("Polygon", "MultiPolygon") and 15 <= area <= 60:
            return g[["geometry"]].dissolve(), f"OpenStreetMap geocode ({area:.1f} km²)"
        print(f"Geocoded polygon is {area:.1f} km², outside the plausible 15–60 km² range.")
    except Exception as e:
        print("Geocoding failed:", e)
    print("Using the fallback bounding box. Replace it with a digitised NKDA boundary when you can.")
    return gpd.GeoDataFrame(geometry=[box(*FALLBACK_BBOX)], crs=4326), "fallback bounding box"


boundary, BOUNDARY_SOURCE = load_boundary()
boundary_p = boundary.to_crs(CRS)
buffer_p = gpd.GeoDataFrame(geometry=boundary_p.buffer(BUFFER_M), crs=CRS)
hexes = make_hex_grid(boundary_p, HEX_WIDTH)
hexes["cx"], hexes["cy"] = hexes.centroid.x, hexes.centroid.y
STUDY_AREA_KM2 = boundary_p.area.sum() / 1e6
print(f"Boundary: {BOUNDARY_SOURCE}; area {STUDY_AREA_KM2:.1f} km²; {len(hexes)} hexagons of {HEX_WIDTH} m")
boundary.to_file(f"{OUT}/data/boundary.geojson", driver="GeoJSON")

# %% [markdown]
# ## 3. Earth Engine setup

# %%
import ee
import geemap

try:
    ee.Initialize(project=PROJECT_ID)
except Exception:
    ee.Authenticate()
    ee.Initialize(project=PROJECT_ID)


def to_ee_fc(gdf):
    return ee.FeatureCollection(json.loads(gdf.to_crs(4326).to_json()))


AOI = to_ee_fc(boundary).geometry()
AOI_BUF = to_ee_fc(buffer_p).geometry()
RING = AOI_BUF.difference(AOI, 1)
HEX_FC = to_ee_fc(hexes[["hex_id", "geometry"]])

S2_BANDS = ["B2", "B3", "B4", "B5", "B6", "B7", "B8", "B11", "B12"]
DW_BANDS = ["water", "trees", "grass", "flooded_vegetation", "crops", "shrub_and_scrub", "built", "bare", "snow_and_ice"]


def season(year, shift=0):
    y = year + shift
    return f"{y - 1}-11-01", f"{y}-03-01"


def s2_collection(year, shift=0):
    start, end = season(year, shift)
    if year + shift >= 2019:
        col = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")

        def mask(img):
            scl = img.select("SCL")
            ok = scl.neq(3).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10))
            return img.select(S2_BANDS).updateMask(ok).divide(10000)
        level = "L2A surface reflectance"
    else:
        col = ee.ImageCollection("COPERNICUS/S2_HARMONIZED")

        def mask(img):
            qa = img.select("QA60")
            ok = qa.bitwiseAnd(1 << 10).eq(0).And(qa.bitwiseAnd(1 << 11).eq(0))
            return img.select(S2_BANDS).updateMask(ok).divide(10000)
        level = "L1C top-of-atmosphere"
    col = col.filterBounds(AOI_BUF).filterDate(start, end).filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 30))
    return col.map(mask), (start, end), level


def s2_composite(year):
    for shift in (0, 1, -1):
        col, period, level = s2_collection(year, shift)
        n = col.size().getInfo()
        if n >= 3:
            break
    img = col.median()
    img = img.addBands([img.normalizedDifference(["B8", "B4"]).rename("NDVI"),
                        img.normalizedDifference(["B11", "B8"]).rename("NDBI"),
                        img.normalizedDifference(["B3", "B11"]).rename("MNDWI")])
    return img.clip(AOI_BUF), n, period, level


def dw_labels(period):
    dw = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1").filterBounds(AOI_BUF).filterDate(*period)
    lab = dw.select("label").mode().remap([0, 1, 2, 3, 4, 5, 6, 7], [0, 1, 1, 0, 2, 1, 3, 4]).rename("lc")
    conf = dw.select(DW_BANDS).mean().reduce(ee.Reducer.max())
    return lab.updateMask(conf.gte(DW_CONF)).clip(AOI_BUF), lab.clip(AOI_BUF)


def class_areas(lc, geom):
    res = ee.Image.pixelArea().divide(1e6).addBands(lc).reduceRegion(
        reducer=ee.Reducer.sum().group(groupField=1, groupName="cls"),
        geometry=geom, scale=10, maxPixels=1e10, tileScale=4).getInfo()
    return {int(g["cls"]): g["sum"] for g in res["groups"]}


def f1_from_matrix(m):
    m = np.asarray(m, float)
    tp = np.diag(m)
    prec = np.divide(tp, m.sum(0), out=np.zeros_like(tp), where=m.sum(0) > 0)
    rec = np.divide(tp, m.sum(1), out=np.zeros_like(tp), where=m.sum(1) > 0)
    return np.divide(2 * prec * rec, prec + rec, out=np.zeros_like(tp), where=(prec + rec) > 0)


# %% [markdown]
# ## 4. Module A — land cover classification and built-up growth

# %%
WORLDCOVER = ee.ImageCollection("ESA/WorldCover/v200").first().remap(
    [10, 20, 30, 40, 50, 60, 80, 90, 95], [1, 1, 1, 2, 3, 4, 0, 0, 1]).rename("wc")

lulc, composites, acc_rows, area_rows, f1_rows = {}, {}, [], [], []
for year in YEARS:
    comp, n_img, period, level = s2_composite(year)
    train_lbl, dw_full = dw_labels(period)
    samples = comp.addBands(train_lbl).stratifiedSample(
        numPoints=SAMPLES_PER_CLASS, classBand="lc", region=AOI_BUF, scale=10,
        seed=42, geometries=False, tileScale=4).randomColumn("rand", 42)
    train = samples.filter(ee.Filter.lt("rand", 0.7))
    test = samples.filter(ee.Filter.gte("rand", 0.7))
    feats = comp.bandNames()
    rf = ee.Classifier.smileRandomForest(numberOfTrees=100, seed=42).train(train, "lc", feats)
    lc = comp.classify(rf).rename("lc").toByte()
    cm = test.classify(rf).errorMatrix("lc", "classification")
    cm_info = ee.Dictionary({"m": cm.array(), "oa": cm.accuracy(), "k": cm.kappa()}).getInfo()
    agree_dw = lc.eq(dw_full).reduceRegion(ee.Reducer.mean(), AOI, 10, maxPixels=1e10, tileScale=4).getInfo()["lc"]
    agree_wc = None
    if period[1].startswith(("2021", "2022")):
        agree_wc = lc.eq(WORLDCOVER).reduceRegion(ee.Reducer.mean(), AOI, 10, maxPixels=1e10, tileScale=4).getInfo()["lc"]
    lulc[year], composites[year] = lc, comp
    areas = class_areas(lc, AOI)
    acc_rows.append({"Year": year, "Imagery": f"{n_img} Sentinel-2 scenes, {period[0]} to {period[1]} ({level})",
                     "Overall accuracy (%)": 100 * cm_info["oa"], "Kappa": cm_info["k"],
                     "Agreement with Dynamic World (%)": 100 * agree_dw,
                     "Agreement with ESA WorldCover 2021 (%)": None if agree_wc is None else 100 * agree_wc})
    f1 = f1_from_matrix(cm_info["m"])
    f1_rows.append({"Year": year, **{CLASS_NAMES[i]: f1[i] for i in range(min(len(f1), 5))}})
    for c in range(5):
        area_rows.append({"Year": year, "Class": CLASS_NAMES[c], "Area (km²)": areas.get(c, 0.0)})
    print(f"{year}: OA {100 * cm_info['oa']:.1f}%, kappa {cm_info['k']:.2f}, {n_img} scenes")

acc_df = pd.DataFrame(acc_rows)
f1_df = pd.DataFrame(f1_rows)
area_long = pd.DataFrame(area_rows)
area_df = area_long.pivot(index="Class", columns="Year", values="Area (km²)").reindex(CLASS_NAMES)
y0, y1 = YEARS[0], YEARS[-1]
area_df[f"Change {y0}–{y1} (%)"] = 100 * (area_df[y1] - area_df[y0]) / area_df[y0].replace(0, np.nan)
area_df.columns = [f"{c} area (km²)" if isinstance(c, (int, np.integer)) else c for c in area_df.columns]
area_df = area_df.reset_index()

trans = ee.Image.pixelArea().divide(1e6).addBands(lulc[y0].multiply(10).add(lulc[y1])).reduceRegion(
    reducer=ee.Reducer.sum().group(groupField=1, groupName="code"), geometry=AOI, scale=10,
    maxPixels=1e10, tileScale=4).getInfo()["groups"]
trans_df = pd.DataFrame(0.0, index=[f"{c} ({y0})" for c in CLASS_NAMES], columns=[f"{c} ({y1})" for c in CLASS_NAMES])
for g in trans:
    a, b = divmod(int(g["code"]), 10)
    trans_df.iloc[a, b] = g["sum"]

b0 = area_long.query("Year == @y0 and Class == 'Built-up'")["Area (km²)"].iloc[0]
b1 = area_long.query("Year == @y1 and Class == 'Built-up'")["Area (km²)"].iloc[0]
BUILT_CAGR = 100 * ((b1 / b0) ** (1 / (y1 - y0)) - 1) if b0 > 0 else np.nan

acc_df.to_csv(f"{OUT}/tables/lulc_accuracy.csv", index=False)
f1_df.to_csv(f"{OUT}/tables/lulc_f1_by_class.csv", index=False)
area_df.to_csv(f"{OUT}/tables/lulc_areas.csv", index=False)
trans_df.to_csv(f"{OUT}/tables/lulc_transition_km2.csv")
display(acc_df, area_df, trans_df.round(2))

# %% [markdown]
# ## 5. Module B — land surface temperature and heat island

# %%
L8 = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
L9 = ee.ImageCollection("LANDSAT/LC09/C02/T1_L2")


def to_lst(img):
    qa = img.select("QA_PIXEL")
    ok = qa.bitwiseAnd(1 << 1).eq(0).And(qa.bitwiseAnd(1 << 3).eq(0)).And(qa.bitwiseAnd(1 << 4).eq(0))
    return img.select("ST_B10").multiply(0.00341802).add(149.0).subtract(273.15).rename("LST").updateMask(ok)


def lst_image(year):
    for start, end in ((f"{year}-03-01", f"{year}-06-01"), (f"{year}-02-01", f"{year}-07-01")):
        col = L8.merge(L9).filterBounds(AOI_BUF).filterDate(start, end).filter(ee.Filter.lt("CLOUD_COVER", 40))
        n = col.size().getInfo()
        if n >= 2:
            break
    return col.map(to_lst).mean().clip(AOI_BUF), n, (start, end)


lst, lst_rows = {}, []
for year in YEARS:
    img, n, per = lst_image(year)
    lst[year] = img
    built = img.updateMask(lulc[year].eq(3)).reduceRegion(ee.Reducer.mean(), AOI, 30, maxPixels=1e10).getInfo()["LST"]
    rural = img.updateMask(lulc[year].eq(1)).reduceRegion(ee.Reducer.mean(), RING, 30, maxPixels=1e10).getInfo()["LST"]
    lst_rows.append({"Year": year, "Landsat scenes": n, "Period": f"{per[0]} to {per[1]}",
                     "Mean LST, built-up (°C)": built, "Mean LST, vegetated reference (°C)": rural,
                     "Surface UHI intensity (°C)": None if built is None or rural is None else built - rural})
    print(f"{year}: {n} Landsat scenes, SUHI = {lst_rows[-1]['Surface UHI intensity (°C)']}")
lst_df = pd.DataFrame(lst_rows)
lst_df.to_csv(f"{OUT}/tables/lst_uhi.csv", index=False)
display(lst_df)

# %% [markdown]
# ## 6. Zonal statistics on the hexagon grid

# %%
POP = ee.ImageCollection("WorldPop/GP/100m/pop").filter(ee.Filter.eq("country", "IND")) \
    .filter(ee.Filter.eq("year", 2020)).first().rename("pop")


def zonal(year):
    lc = lulc[year]
    stack = composites[year].select(["NDVI", "NDBI", "MNDWI"]).addBands(lst[year]).addBands(
        [lc.eq(0).rename("f_water"), lc.eq(1).rename("f_veg"), lc.eq(3).rename("f_built")])
    fc = stack.reduceRegions(collection=HEX_FC, reducer=ee.Reducer.mean(), scale=10, tileScale=4)
    rows = [f["properties"] for f in fc.getInfo()["features"]]
    return pd.DataFrame(rows).set_index("hex_id")


hex_year = {y: zonal(y) for y in YEARS}
pop = POP.reduceRegions(collection=HEX_FC, reducer=ee.Reducer.sum(), scale=100).getInfo()["features"]
pop = pd.Series({f["properties"]["hex_id"]: f["properties"].get("sum", 0) for f in pop}, name="pop")

H = hexes.set_index("hex_id").join(hex_year[y1]).join(pop)
H["d_built"] = H["f_built"] - hex_year[y0]["f_built"].reindex(H.index)
H["f_bluegreen"] = H["f_water"] + H["f_veg"]
H["UTFVI"] = (H["LST"] - H["LST"].mean()) / (H["LST"] + 273.15)
missing = H[["NDVI", "LST"]].isna().any(axis=1).sum()
if missing:
    print(f"{missing} hexes had masked pixels (cloud); filled with the median for the index")
print(H[["NDVI", "NDBI", "MNDWI", "LST", "f_built", "pop"]].describe().round(3))

# %% [markdown]
# ## 7. Module B (cont.) — LST regression

# %%
reg = H[["LST", "NDVI", "NDBI", "MNDWI"]].dropna()
ols = sm.OLS(reg["LST"], sm.add_constant(reg[["NDVI", "NDBI", "MNDWI"]])).fit()
print(ols.summary())
r_ndvi = stats.pearsonr(reg["NDVI"], reg["LST"])
r_ndbi = stats.pearsonr(reg["NDBI"], reg["LST"])
reg_g = gpd.GeoDataFrame(reg.join(hexes.set_index("hex_id")["geometry"]), crs=CRS).reset_index()
w_reg = build_weights(reg_g)
resid_moran = Moran(ols.resid.to_numpy(), w_reg, permutations=999)

heat_df = pd.DataFrame([
    {"Statistic": f"Mean pre-monsoon LST, built-up, {y1} (°C)", "Value": lst_df.iloc[-1]["Mean LST, built-up (°C)"]},
    {"Statistic": f"Mean pre-monsoon LST, vegetated reference, {y1} (°C)", "Value": lst_df.iloc[-1]["Mean LST, vegetated reference (°C)"]},
    {"Statistic": f"Surface UHI intensity, {y1} (°C)", "Value": lst_df.iloc[-1]["Surface UHI intensity (°C)"]},
    {"Statistic": "Pearson r, LST vs NDVI (hexes)", "Value": r_ndvi[0]},
    {"Statistic": "Pearson r, LST vs NDBI (hexes)", "Value": r_ndbi[0]},
    {"Statistic": "OLS R², LST ~ NDVI + NDBI + MNDWI", "Value": ols.rsquared},
    {"Statistic": "Moran's I of OLS residuals", "Value": resid_moran.I},
    {"Statistic": "Pseudo p-value of residual Moran's I", "Value": resid_moran.p_sim},
])
heat_df.to_csv(f"{OUT}/tables/heat_statistics.csv", index=False)
pd.DataFrame({"coef": ols.params, "p": ols.pvalues}).to_csv(f"{OUT}/tables/lst_ols_coefficients.csv")
display(heat_df)

# %% [markdown]
# ## 8. Module C — 15-minute walking accessibility

# %%
buf_wgs = buffer_p.to_crs(4326).geometry.iloc[0]
G = ox.graph_from_polygon(buf_wgs, network_type="walk")
Gp = ox.project_graph(G, to_crs=CRS)
try:
    Gu = ox.convert.to_undirected(Gp)
except AttributeError:
    Gu = ox.utils_graph.get_undirected(Gp)
hex_nodes = ox.distance.nearest_nodes(Gu, H["cx"].to_numpy(), H["cy"].to_numpy())
WALK_M = WALK_SPEED_KMH * 1000 / 60 * WALK_MINUTES

poi_counts, poi_layers = {}, []
for key, tags in SERVICES.items():
    try:
        pois = ox.features_from_polygon(buf_wgs, tags).to_crs(CRS)
    except Exception as e:
        print(f"{key}: no features found ({e})")
        H[f"d_{key}"] = np.inf
        poi_counts[key] = 0
        continue
    pts = pois.geometry.centroid
    sources = set(ox.distance.nearest_nodes(Gu, pts.x.to_numpy(), pts.y.to_numpy()))
    dist = nx.multi_source_dijkstra_path_length(Gu, sources, weight="length")
    H[f"d_{key}"] = [dist.get(n, np.inf) for n in hex_nodes]
    poi_counts[key] = len(pois)
    poi_layers.append(gpd.GeoDataFrame({"service": key}, geometry=pts, crs=CRS))
    print(f"{key}: {len(pois)} features")

H["score15"] = sum((H[f"d_{k}"] <= WALK_M).astype(float) for k in SERVICES) / len(SERVICES)
H["d_transit_cap"] = H["d_transit"].clip(upper=3000)
popw = H["pop"].fillna(0)
acc_rows = []
for k in SERVICES:
    d = H[f"d_{k}"]
    acc_rows.append({"Service category": SERVICE_LABELS[k], "OSM features in area + buffer": poi_counts[k],
                     "Median walk distance (m)": float(np.median(d[np.isfinite(d)])) if np.isfinite(d).any() else np.nan,
                     "Population within 15 min (%)": 100 * popw[d <= WALK_M].sum() / popw.sum()})
acc_rows.append({"Service category": "All five categories", "OSM features in area + buffer": "",
                 "Median walk distance (m)": np.nan,
                 "Population within 15 min (%)": 100 * popw[H["score15"] == 1].sum() / popw.sum()})
access_df = pd.DataFrame(acc_rows)
access_df.to_csv(f"{OUT}/tables/accessibility.csv", index=False)
display(access_df)

# Zone comparison (H3): Action Areas if provided, else core / middle / edge by distance from centroid
if ACTION_AREAS_FILE:
    aa = gpd.read_file(ACTION_AREAS_FILE).to_crs(CRS)
    cent = gpd.GeoDataFrame(H[["cx"]], geometry=gpd.points_from_xy(H["cx"], H["cy"]), crs=CRS)
    H["zone"] = gpd.sjoin(cent, aa[["name", "geometry"]], how="left", predicate="within")["name"] \
        .groupby(level=0).first().reindex(H.index)
    ZONE_METHOD = "Action Areas"
else:
    c = boundary_p.geometry.iloc[0].centroid
    dist_c = np.hypot(H["cx"] - c.x, H["cy"] - c.y)
    H["zone"] = pd.qcut(dist_c, 3, labels=["Core", "Middle", "Edge"]).astype(str)
    ZONE_METHOD = "distance-from-centroid terciles"
zone_groups = [g["score15"].to_numpy() for _, g in H.dropna(subset=["zone"]).groupby("zone")]
kw = stats.kruskal(*zone_groups) if len(zone_groups) > 1 else None
zone_df = H.groupby("zone")["score15"].agg(["count", "mean", "median"]).reset_index() \
    .rename(columns={"zone": "Zone", "count": "Hexes", "mean": "Mean 15-min score", "median": "Median 15-min score"})
zone_df.to_csv(f"{OUT}/tables/accessibility_by_zone.csv", index=False)
print(zone_df, "\nKruskal-Wallis:", kw)

# %% [markdown]
# ## 9. Smart Liveability Index (AHP) and sensitivity

# %%
W_AHP, CR = ahp_weights(AHP_MATRIX)
assert CR < 0.10, f"AHP judgements inconsistent (CR = {CR:.3f}); revise AHP_MATRIX"
for col, _ in SLI_SPEC:
    H[col] = H[col].fillna(H[col].median())
H["SLI"] = compute_sli(H, SLI_SPEC, W_AHP)
H["SLI_quintile"] = quintiles(H["SLI"]) + 1
ahp_df = pd.DataFrame({"Indicator": SLI_LABELS, "Column": [c for c, _ in SLI_SPEC], "AHP weight": W_AHP})
sens_df = sensitivity(H, SLI_SPEC, W_AHP)
ahp_df.to_csv(f"{OUT}/tables/ahp_weights.csv", index=False)
sens_df.to_csv(f"{OUT}/tables/sli_sensitivity.csv", index=False)
print(f"Consistency ratio = {CR:.3f}")
display(ahp_df, sens_df)

# %% [markdown]
# ## 10. Module D — spatial clustering

# %%
HG = gpd.GeoDataFrame(H.reset_index(), geometry="geometry", crs=CRS)
W = build_weights(HG)
clus_rows = []
for col in ["LST", "score15", "SLI"]:
    summary, lisa_lab, hot = cluster_stats(HG, col, W)
    HG[f"lisa_{col}"], HG[f"gi_{col}"] = lisa_lab, hot
    clus_rows.append(summary)
cluster_df = pd.DataFrame(clus_rows).replace({"Variable": {"LST": "LST", "score15": "15-minute score",
                                                           "SLI": "Smart Liveability Index"}})
cluster_df.to_csv(f"{OUT}/tables/spatial_clustering.csv", index=False)
HG.drop(columns=["cx", "cy"]).to_file(f"{OUT}/data/hex_results.gpkg", driver="GPKG")
display(cluster_df)

# %% [markdown]
# ## 11. Figures

# %%
F = f"{OUT}/figures"
lc_cmap = ListedColormap(CLASS_COLORS)

# Study area
fig, ax = plt.subplots(figsize=(7, 7))
ox.plot_graph(Gp, ax=ax, node_size=0, edge_color="#9a9a9a", edge_linewidth=0.3, show=False, close=False, bgcolor="white")
buffer_p.boundary.plot(ax=ax, color="#888888", linestyle="--", linewidth=0.8)
boundary_p.boundary.plot(ax=ax, color="#d7301f", linewidth=1.5)
if poi_layers:
    pd.concat(poi_layers).plot(ax=ax, column="service", markersize=4, legend=True, legend_kwds={"fontsize": 7})
ax.set_title(f"Study area: New Town Kolkata ({BOUNDARY_SOURCE}), walk network and services", fontsize=10)
fig.savefig(f"{F}/01_study_area.png", dpi=200, bbox_inches="tight")
plt.close(fig)

# LULC maps (downloaded rasters)
import rasterio
fig, axes = plt.subplots(1, len(YEARS), figsize=(5 * len(YEARS), 5.5))
for ax, year in zip(np.atleast_1d(axes), YEARS):
    path = f"{OUT}/data/lulc_{year}.tif"
    try:
        # shift classes to 1..5 so 0 can mean "outside the boundary"
        img = lulc[year].clip(AOI).add(1).unmask(0).toByte()
        geemap.ee_export_image(img, filename=path, scale=10, crs=CRS, region=AOI.bounds(), verbose=False)
        with rasterio.open(path) as src:
            arr = src.read(1).astype(float) - 1
            arr[arr < 0] = np.nan
            ext = [src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top]
        ax.imshow(arr, cmap=lc_cmap, vmin=-0.5, vmax=4.5, extent=ext, interpolation="nearest")
        boundary_p.boundary.plot(ax=ax, color="black", linewidth=0.8)
    except Exception as e:
        ax.text(0.5, 0.5, f"Download failed:\n{e}", ha="center", transform=ax.transAxes, fontsize=8)
    ax.set_title(f"Land cover {year}")
    ax.set_axis_off()
fig.legend(handles=[Patch(color=c, label=n) for n, c in zip(CLASS_NAMES, CLASS_COLORS)], loc="lower center", ncol=5)
fig.savefig(f"{F}/02_lulc_maps.png", dpi=200, bbox_inches="tight")
plt.close(fig)

# LULC area bars
area_long.pivot(index="Year", columns="Class", values="Area (km²)")[CLASS_NAMES].plot(
    kind="bar", color=CLASS_COLORS, figsize=(7, 4), ylabel="Area (km²)", title="Land cover area by year").figure \
    .savefig(f"{F}/03_lulc_areas.png", dpi=200, bbox_inches="tight")
plt.close("all")

hex_map(HG, "d_built", f"Change in built-up share per hexagon, {y0}–{y1}", f"{F}/04_built_change.png",
        boundary_p, cmap="Reds", legend_label="Δ built-up fraction")
hex_map(HG, "LST", f"Mean pre-monsoon LST, {y1}", f"{F}/05_lst.png", boundary_p, cmap="inferno", legend_label="°C")

fig, ax = plt.subplots(figsize=(5.5, 4.5))
ax.scatter(reg["NDVI"], reg["LST"], s=8, alpha=0.6, color="#d7301f")
m, b = np.polyfit(reg["NDVI"], reg["LST"], 1)
xs = np.linspace(reg["NDVI"].min(), reg["NDVI"].max(), 50)
ax.plot(xs, m * xs + b, color="black")
ax.set_xlabel("Mean NDVI per hexagon")
ax.set_ylabel("Mean LST (°C)")
ax.set_title(f"LST vs NDVI, r = {r_ndvi[0]:.2f}")
fig.savefig(f"{F}/06_lst_ndvi_scatter.png", dpi=200, bbox_inches="tight")
plt.close(fig)

fig, axes = plt.subplots(1, 5, figsize=(22, 5))
for ax, k in zip(axes, SERVICES):
    HG.assign(dkm=HG[f"d_{k}"].clip(upper=3000) / 1000).plot(column="dkm", ax=ax, cmap="viridis_r", legend=True,
                                                             legend_kwds={"shrink": 0.6, "label": "km"})
    boundary_p.boundary.plot(ax=ax, color="black", linewidth=0.6)
    ax.set_title(f"Walk distance: {SERVICE_LABELS[k]}")
    ax.set_axis_off()
fig.savefig(f"{F}/07_service_distances.png", dpi=200, bbox_inches="tight")
plt.close(fig)

hex_map(HG, "score15", "15-minute score (share of 5 services within 1.2 km walk)", f"{F}/08_score15.png",
        boundary_p, cmap="YlGn", legend_label="score")
hex_map(HG, "SLI_quintile", "Smart Liveability Index (quintile, 5 = best)", f"{F}/09_sli_quintiles.png",
        boundary_p, cmap="RdYlGn", legend_label="quintile")
LISA_COLORS = {"High-High": "#d7191c", "Low-Low": "#2c7bb6", "High-Low": "#fdae61", "Low-High": "#abd9e9",
               "Not significant": "#eeeeee"}
GI_COLORS = {"Hot spot": "#d7191c", "Cold spot": "#2c7bb6", "Not significant": "#eeeeee"}
hex_map(HG, "lisa_SLI", "LISA clusters of the SLI (FDR 5%)", f"{F}/10_sli_lisa.png", boundary_p, categories=LISA_COLORS)
hex_map(HG, "gi_SLI", "Getis-Ord Gi* hot and cold spots of the SLI (FDR 5%)", f"{F}/11_sli_gi.png",
        boundary_p, categories=GI_COLORS)
hex_map(HG, "gi_LST", "Getis-Ord Gi* hot and cold spots of LST (FDR 5%)", f"{F}/12_lst_gi.png",
        boundary_p, categories=GI_COLORS)
print(sorted(os.listdir(F)))

# %% [markdown]
# ## 12. Write `results.md` and zip the outputs

# %%
fmt = lambda v, d=2: "" if v is None or (isinstance(v, float) and np.isnan(v)) else f"{v:,.{d}f}"
low_low = HG.loc[HG["lisa_SLI"] == "Low-Low"]
report = f"""# Results — New Town Kolkata smart liveability analysis

Study area: {BOUNDARY_SOURCE}, {STUDY_AREA_KM2:.1f} km², {len(HG)} hexagons ({HEX_WIDTH} m).
Training labels: Dynamic World pixels with probability ≥ {DW_CONF}; accuracy is measured against held-out
Dynamic World labels (30%), with ESA WorldCover 2021 as an independent check.

## 7.1 Land cover change (RQ1)

{md_table(area_df)}

Built-up compound annual growth {y0}–{y1}: {fmt(BUILT_CAGR)}% per year.

**Accuracy**

{md_table(acc_df)}

**Per-class F1**

{md_table(f1_df)}

**Transition matrix {y0} → {y1} (km²; rows = {y0}, columns = {y1})**

{md_table(trans_df.reset_index().rename(columns={'index': 'From / to'}))}

## 7.2 Heat island (RQ2)

{md_table(heat_df, 3)}

**Surface UHI by year**

{md_table(lst_df)}

OLS coefficients: {', '.join(f'{k} = {v:.2f} (p = {p:.3f})' for k, v, p in zip(ols.params.index, ols.params, ols.pvalues))}.

## 7.3 Accessibility (RQ3)

Walking threshold: {WALK_MINUTES} min at {WALK_SPEED_KMH} km/h = {WALK_M:.0f} m network distance.

{md_table(access_df, 1)}

**By zone ({ZONE_METHOD})**

{md_table(zone_df, 2)}

Kruskal-Wallis H = {fmt(kw.statistic if kw else None)}, p = {fmt(kw.pvalue if kw else None, 4)}.

## 7.4 Spatial clustering (RQ4)

{md_table(cluster_df, 3)}

Low-Low SLI hexes (priority zones): {len(low_low)}, covering {len(low_low) * HG.area.mean() / 1e6:.2f} km²
and an estimated {low_low['pop'].sum():,.0f} residents (WorldPop 2020).

## 7.5 AHP weights and robustness

{md_table(ahp_df, 3)}

Consistency ratio: {CR:.3f}.

{md_table(sens_df, 3)}
"""
with open(f"{OUT}/results.md", "w") as fh:
    fh.write(report)
shutil.make_archive("newtown_outputs", "zip", OUT)
print(report)
try:
    from google.colab import files
    files.download("newtown_outputs.zip")
except Exception:
    print("Outputs zipped to newtown_outputs.zip")
