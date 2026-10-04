"""INVESTIGATION — the automated digitising route was tried and did NOT validate.

Do not treat this module as a working pipeline. It is kept as a record of what was
attempted, why it failed, and where the remaining option lies.

Goal
----
Digitise the New Town Planning Area boundary from the official NKDA plan-area map
(`maps-of-new-town-planning-area.pdf`) and feed it to the notebook as BOUNDARY_FILE, in
place of the fallback bounding box.

The intended method was
1. LUDCP 2012 (WBHIDCO, `report11.pdf`) Table 2 schedules the 45 mouzas with their J.L.
   (Jote/Lot) numbers and areas, summing to 60.354 km². Verified exactly — see
   `ludcp_table.py`.
2. The map labels its polygons with those same J.L. numbers, so each number should
   identify one polygon.
3. Summing the matched polygons in PDF units² then yields metres-per-unit from the
   official total, and the union of the matched polygons is the boundary.

Why it failed
-------------
Step 2 does not hold. Findings from the parsed drawing (8 layers, 75,298 rings, 351
labels):

* The sheet carries **no georeference at all**: no /GPTS, no /LPTS, no UTM- or
  lat/lon-magnitude numbers, and the single /Measure array is the default
  0.01389 points-per-unit viewport spec. There is no coordinate grid to register on.
* The map **does not draw the 45 mouzas as identifiable polygons**. Across the whole
  sheet the largest filled polygon is 13,299 units²; the large features are ~930 closed
  rings, but the biggest ones are *containers* — one 5,536,952-unit² ring encloses the
  labels for J.L. 23, 25, 26, 27, 32 and 43 simultaneously, and another 1,545,166-unit²
  ring holds J.L. 40, 41 and 42.
* Consequently the "smallest ring containing the label" heuristic picks a container for
  many mouzas. The implied scale per mouza, sqrt(area_km2e6 / ring_units2), is not
  consistent: median 1.517 m/unit, interquartile range 0.687–2.067, outliers to 13.9,
  and only 9% of mouzas fall within 5% of the median. A real, correct extraction would
  cluster tightly.
* Independently, OSM does not carry these villages: of ~41 map-labelled place names,
  Nominatim returned nothing for 37 (Bhojerhat, Hatgachha, Raigacchi, Langalpota,
  Panapukhuria, Arbelia, Bagjola Khal, Chowreswar Canal, ...), so the labelled points
  cannot georeference the sheet either.

A plausible sheet scale is about 2.3 m/unit (the content spans roughly 30 x 29 km), at
which the 5,536,952-unit² ring would be ~29.3 km² — suspiciously close to the NKDA
statutory area of 29.34 km². That is a coincidence worth checking by hand, not evidence:
it rests on a scale estimated from a single area match, not on a derivation.

Remaining options, in order of preference
-----------------------------------------
1. Digitise by hand in QGIS from the official sheet (render it with `pdfmap`, georeference
   on OSM features that do resolve — Eco Park, Rajarhat, Kazi Nazrul Islam Sarani,
   Krishnapur Canal, Tona PHC, Eastern Metropolitan Bypass). Accurate and citable.
2. Ask the collaborator or course staff for the shapefile.
3. Trace the boundary from the LUDCP's written description, noting that the eastern side
   is not described and that OSM lacks the named canals.
from __future__ import annotations

import math
import re
import zlib
from dataclasses import dataclass, field

import numpy as np
import requests
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

import pdfmap

MAP_URL = pdfmap.PDF_URL

# ---- LUDCP 2012 Table 2, in file order: (J.L. number, area km2, mouza name) ------
TABLE2: list[tuple[int, float, str]] = [
    (12, 1.370, "Raigacchi"), (13, 1.710, "Rekjuani"), (21, 0.204, ""),
    (22, 0.960, ""), (23, 1.857, "Ghuni"), (24, 0.650, ""), (25, 0.500, ""),
    (33, 0.799, ""), (34, 0.667, "Baligari"), (35, 0.450, ""),
    (36, 1.509, "Patharghata"), (55, 1.206, ""), (20, 0.282, ""),
    (19, 0.740, ""), (15, 0.470, ""), (27, 1.720, ""), (26, 0.700, "Dharsa"),
    (32, 1.480, ""), (28, 1.080, "Bhatenda"), (29, 0.620, "Khamar"),
    (44, 1.260, "Bishnupur"), (30, 0.613, "Kalaberia"), (31, 1.290, "Basina"),
    (43, 0.635, "Chota Chanpur"), (42, 1.720, "Jamalpara"), (41, 0.800, "Umarhati"),
    (40, 1.320, "Kalikapur"), (39, 1.540, ""), (49, 2.160, "Sikharpur"),
    (38, 0.540, "Jhalgachhi"), (37, 1.580, "Ganragari"), (53, 2.080, "Nawabad"),
    (54, 2.080, "Hudarait"), (2, 0.750, "Koch Pukur"), (3, 0.930, "Jot Bhim"),
    (9, 0.812, ""), (13, 0.690, "Tara Hadia"), (12, 0.480, "Dakshin Khairpur"),
    (11, 0.580, "Abua"), (24, 4.780, "Pitha Pukuria"), (25, 1.660, "Jiran"),
    (45, 7.690, "Bamunia"), (69, 1.530, "Chalta Beria"), (71, 1.290, "Chak Maricha"),
    (10, 2.570, "Bhaga Banpur"),
]
OFFICIAL_TOTAL_KM2 = 60.354
JL_TARGETS = sorted({jl for jl, _a, _n in TABLE2})

JL_FONT_LO, JL_FONT_HI = 50, 68      # J.L. number labels (mouza names are size 88)
MOUZA_FILL = (0.46, 0.46, 0.46)      # grey mouza polygon fill


# --------------------------------------------------------------------------- PDF

def fetch_map(path: str | None = None) -> bytes:
    if path and __import__("os").path.exists(path):
        return open(path, "rb").read()
    r = requests.get(MAP_URL, headers=pdfmap.UA, timeout=240)
    r.raise_for_status()
    if path:
        open(path, "wb").write(r.content)
    return r.content


def content_streams(pdf: bytes) -> list[bytes]:
    objs = {int(m.group(1)): m.group(3)
            for m in re.finditer(rb"(\d+)\s+(\d+)\s+obj\b(.*?)\bendobj", pdf, re.S)}

    def stream_of(body: bytes) -> bytes | None:
        m = re.search(rb"stream\r?\n(.*?)\r?\nendstream", body, re.S)
        if not m:
            return None
        try:
            return zlib.decompress(m.group(1))
        except Exception:
            return m.group(1)

    pm = re.search(rb"/Type\s*/Page(?![s]).*?/Contents\s*\[(.*?)\]", pdf, re.S)
    if not pm:
        raise RuntimeError("page /Contents array not found")
    refs = [int(x) for x in re.findall(rb"(\d+)\s+\d+\s+R", pm.group(1))]
    return [stream_of(objs.get(r, b"")) or b"" for r in refs]


@dataclass
class MapData:
    rings: list[pdfmap.Ring] = field(default_factory=list)
    labels: list[pdfmap.Label] = field(default_factory=list)
    per_layer: dict[int, pdfmap.MapContent] = field(default_factory=dict)


def load_map(pdf_bytes: bytes) -> MapData:
    md = MapData()
    for li, s in enumerate(content_streams(pdf_bytes)):
        m = pdfmap.parse(s)
        md.rings.extend(m.rings)
        md.labels.extend(m.labels)
        md.per_layer[li] = m
    return md


# ------------------------------------------------------------------ association

def jl_labels(md: MapData) -> list[tuple[int, float, float]]:
    """J.L. number labels.

    Font size does not separate them reliably: small J.L. numbers are set at the same
    size as mouza names (88) and only the three-digit ones are smaller (59). Matching on
    the value itself is unambiguous, because J.L. numbers are 1-3 digits and the target
    set is known exactly.
    """
    targets = set(JL_TARGETS)
    out = []
    for lb in md.labels:
        t = lb.text.strip()
        if t.isdigit() and int(t) in targets:
            out.append((int(t), lb.x, lb.y, lb.font_size))
    return out


def mouza_polygons(md: MapData) -> list[Polygon]:
    polys: list[Polygon] = []
    for r in md.rings:
        if r.source != "fill" or not r.fill:
            continue
        if tuple(round(c, 2) for c in r.fill) != MOUZA_FILL:
            continue
        if len(r.points) < 4:
            continue
        g = Polygon(r.points)
        if not g.is_valid:
            g = g.buffer(0)
        if g.is_empty or g.area <= 0:
            continue
        polys.append(g)
    return polys


def associate(md: MapData) -> tuple[dict[int, list[int]], dict]:
    """Assign each J.L. number label to the mouza polygon containing it."""
    polys = mouza_polygons(md)
    labels = [(jl, x, y) for jl, x, y, _sz in jl_labels(md)]

    picked: dict[int, list[int]] = {}
    stats = {"labels_in_targets": len(labels), "polygons": len(polys),
             "labels_inside": 0, "labels_unmatched_jl": []}
    for jl, x, y in labels:
        pt = Point(x, y)
        hit = None
        for i, g in enumerate(polys):
            if g.contains(pt):
                hit = i
                break
        if hit is None:
            continue
        stats["labels_inside"] += 1
        if hit not in picked.setdefault(jl, []):
            picked[jl].append(hit)
    return picked, stats


# ------------------------------------------------------------------- georeference

@dataclass
class Similarity:
    """PDF units -> EPSG:4326 (degrees). scale in degrees per unit."""
    a: float
    b: float
    d: float
    e: float
    xoff: float
    yoff: float

    def apply(self, x: float, y: float) -> tuple[float, float]:
        return (self.a * x + self.b * y + self.xoff,
                self.d * x + self.e * y + self.yoff)

    def metres_per_unit(self) -> float:
        import pyproj
        tr = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:32645", always_xy=True)
        lon0, lat0 = self.apply(0.0, 0.0)
        lon1, lat1 = self.apply(1000.0, 0.0)
        lat2, _ = self.apply(0.0, 1000.0)
        x0, y0 = tr.transform(lon0, lat0)
        x1, y1 = tr.transform(lon1, lat1)
        x2, y2 = tr.transform(lat0, lat2)
        return 0.5 * (math.hypot(x1 - x0, y1 - y0) + math.hypot(x2 - x0, y2 - y0))


def fit_similarity(src: np.ndarray, dst: np.ndarray) -> tuple[Similarity, np.ndarray]:
    """Least-squares similarity (uniform scale + rotation + translation), no reflection."""
    n = len(src)
    A = np.zeros((2 * n, 4))
    b = np.zeros(2 * n)
    for i, ((x, y), (u, v)) in enumerate(zip(src, dst)):
        A[2 * i] = (x, y, 1, 0)
        A[2 * i + 1] = (0, x, y, 1)
        b[2 * i] = u
        b[2 * i + 1] = v
    sol, *_ = np.linalg.lstsq(A, b, rcond=None)
    a, bb, d, e = sol
    sim = Similarity(a, bb, d, e, float(sol[2]), float(sol[3]))
    # recover translation
    sim = Similarity(a, bb, d, e, 0.0, 0.0)
    resid = np.array([sim.apply(x, y) for (x, y) in src]) - dst
    off = -resid.mean(axis=0)
    sim = Similarity(a, bb, d, e, float(off[0]), float(off[1]))
    resid = np.array([sim.apply(x, y) for (x, y) in src]) - dst
    return sim, resid