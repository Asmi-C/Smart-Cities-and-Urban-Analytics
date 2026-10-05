"""Recover the statutory NKDA boundary from the official NKDA plan-area sheet.

The New Town Kolkata Development Authority (NKDA) area is 29.34 km2, defined legally by
Schedule I Part A of the New Town, Kolkata Development Authority Act, 2007 as 24 mouza
parts taken by Revisional Settlement plot number. The only published *drawing* of that
area is the NKDA plan-area sheet:

    https://nkdamar.org/storage/files/maps-of-new-town-planning-area.pdf

That sheet is an unregistered CAD plot: it carries no /GPTS, no /LPTS and no coordinate
grid, so it cannot be georeferenced from itself. It does however draw the NKDA AREA
boundary as a heavy blue dashed line and, nested inside it, the wider PLANNING AREA
boundary as a dark red dashed line. Both styles were confirmed against the sheet's own
legend swatches, which sit beside the "NKDA AREA" / "PLANNING AREA" text labels at
y = 4718: blue (0, 0, 1) width 19 for NKDA, dark red (0.58, 0, 0) width 25 for PLANNING.

Three things about the drawing drive the implementation
-------------------------------------------------------
1. Both boundaries are drawn as *dotted* lines: thousands of short independent strokes,
   not one closed path object.
2. `pdfmap` emits a large number of **zero-length** strokes for the blue geometry
   (3976 of7953 in layer 6). They are degenerate and must be dropped or they break
   every chaining attempt.
3. Endpoint clustering is useless here. The dashes are so densely spaced (gap ~4u for
   NKDA, ~8u for PLANNING) that union-find over endpoint proximity is *transitive*
   along the whole ring and collapses every endpoint into a single node. What does work
   is **stream order**: the CAD emits each boundary's dashes consecutively along the
   line, so concatenating the surviving strokes in order and bridging the small
   inter-dash gaps reproduces the ring exactly.

Scale and registration
----------------------
Scale is solved from the published NKDA area, `sqrt(29.34e6 / measured_u2)`. The
resulting ring is registered to EPSG:4326 by solving rotation and translation against
named features that exist both on the sheet and in OpenStreetMap, with the scale held
fixed. Residuals are reported, not hidden -- see `registration_report()`.

Only the NKDA ring is the project boundary. The PLANNING AREA ring is retained purely
as a diagnostic in `scale_report()`; it is *not* used to fix the scale, and it is not a
project deliverable.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import zlib
from dataclasses import dataclass, field

import numpy as np
import requests
from shapely.geometry import Polygon, shape

import pdfmap

MAP_URL = pdfmap.PDF_URL
MAP_CACHE = "boundary/map.pdf"

# ---- the two boundaries as drawn on the sheet -----------------------------------
# Colour and width were read off the sheet's own legend swatches, found by searching
# for strokes inside the legend boxes beside the "NKDA AREA" / "PLANNING AREA" labels.
PLANNING = dict(colour=(0.58, 0.0, 0.0), width=25.0, layer=6)
NKDA = dict(colour=(0.0, 0.0, 1.0), width=19.0, layer=6)

# The statutory area: Schedule I Part A of the NKDA Act, 2007, and nkdamar.org/nkda-profile.
NKDA_OFFICIAL_KM2 = 29.34

# Metres per PDF user unit. Solved by solve_scale(); the committed value.
SCALE_M_PER_UNIT = 1.5663

# Gap to bridge between consecutive dashes when rebuilding a ring from stream order.
# The observed stream gaps are <=8.94u for NKDA, so 12u is a safe threshold; the NKDA
# ring is emitted as one continuous run of dashes and must produce a single piece.
JOIN_TOL = 12.0

# Strokes shorter than this are degenerate parser output and are discarded.
MIN_STROKE_U = 1.0

# Local metric frame for registration: equirectangular about this origin is accurate to
# a few metres over a 20 km extent, which is far below the registration residuals.
LAT0, LON0 = 22.58, 88.44
M_PER_DEG_LAT = 111132.0
M_PER_DEG_LON = 111320.0 * math.cos(math.radians(LAT0))

# Ground control: the map label anchor in PDF user units, and the same place in OSM.
# Only *point* features are used. Road and junction labels were tried and rejected --
# their drafter-placed anchors sit 1.7-2.7 km from the feature, which would triple the
# RMS for no gain. See REJECTED_GCP for the record.
GCP: dict[str, tuple[tuple[float, float], tuple[float, float]]] = {
    "Baguiati":   ((8756.0, 14654.0), (88.4276832, 22.6096680)),
    "Kaikhali":   ((9934.0, 14342.0), (88.4346171, 22.6344209)),
    "Arjunpur":   ((9455.0, 15174.0), (88.4248100, 22.6199600)),
    "Ultadanga":  ((7626.0, 16992.0), (88.3841500, 22.6012800)),
    "Tona":       ((8593.0, 6122.0),  (88.5641300, 22.6120700)),
}

REJECTED_GCP = {
    "Kazi Nazrul Islam Sarani": "road label, anchor ~2.7 km from the road",
    "Dum Dum":                  "junction label, anchor ~2.4 km away",
    "Jyangra":                  "'choumatha' intersection label, ~1.7 km away",
}

# Places that must fall inside / outside the registered boundary.
MUST_BE_INSIDE = {"Eco Park": (22.6022363, 88.4647410)}
MUST_BE_OUTSIDE = {
    "Rajarhat": (22.6564623, 88.4467245),
    "Baguiati": (22.6096680, 88.4276832),
    "Dum Dum":  (22.6211141, 88.3928973),
    "Ultadanga": (22.5961300, 88.3852800),
}


# --------------------------------------------------------------------------- PDF

def fetch_map(path: str = MAP_CACHE) -> bytes:
    """Read the sheet from `path`, downloading it once if it is not there yet."""
    if os.path.exists(path):
        return open(path, "rb").read()
    r = requests.get(MAP_URL, headers=pdfmap.UA, timeout=240)
    r.raise_for_status()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(r.content)
    return r.content


def content_streams(pdf: bytes) -> list[bytes]:
    """Inflated content streams of the first page, in drawing order (one per OCG layer)."""
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
class Sheet:
    """The parsed drawing, indexed by content-stream (layer) number."""
    per_layer: dict[int, pdfmap.MapContent] = field(default_factory=dict)

    def rings(self, layer: int):
        m = self.per_layer.get(layer)
        return m.rings if m else []


def load(pdf_path: str = MAP_CACHE) -> Sheet:
    sh = Sheet()
    for li, s in enumerate(content_streams(fetch_map(pdf_path))):
        sh.per_layer[li] = pdfmap.parse(s)
    return sh


# --------------------------------------------------------------------------- ring

@dataclass
class Ring:
    """A recovered boundary: a closed polyline in PDF units, with its provenance."""
    points: list[tuple[float, float]]
    style: dict = field(default_factory=dict)
    n_marks: int = 0
    n_dropped: int = 0
    n_pieces: int = 1
    closure_gap_u: float = 0.0
    perimeter_u: float = 0.0
    registration: dict = field(default_factory=dict)

    @property
    def n_points(self) -> int:
        return len(self.points)

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        xs = [p[0] for p in self.points]
        ys = [p[1] for p in self.points]
        return min(xs), min(ys), max(xs), max(ys)

    @property
    def area_u2(self) -> float:
        return float(Polygon(self.points).buffer(0).area)


def boundary_marks(sheet: Sheet, style: dict) -> tuple[list[list[tuple[float, float]]], int]:
    """Strokes of one colour/width in stream order, with degenerate ones dropped.

    `pdfmap` splits a stroked subpath on every `m`, so each dash arrives as its own
    2-point ring. Roughly half the blue ones come back zero-length; those carry no
    geometry and are counted, not used.
    """
    col, wid, layer = style["colour"], style["width"], style["layer"]
    kept, dropped = [], 0
    for r in sheet.rings(layer):
        if r.source != "stroke" or not r.stroke or len(r.points) < 2:
            continue
        if tuple(round(c, 2) for c in r.stroke) != col:
            continue
        if abs(r.line_width - wid) >= 1.0:
            continue
        length = sum(math.dist(r.points[i], r.points[i + 1]) for i in range(len(r.points) - 1))
        if length < MIN_STROKE_U:
            dropped += 1
            continue
        kept.append([tuple(p) for p in r.points])
    return kept, dropped


def chain_marks(marks: list[list[tuple[float, float]]],
                join_tol: float = JOIN_TOL) -> list[list[tuple[float, float]]]:
    """Concatenate dashes in stream order, splitting wherever the stream jumps.

    The NKDA ring is drawn as one continuous run of dashes, so it yields a single piece.
    The wider PLANNING ring is emitted as several separate runs; splitting rather than
    raising keeps that ring usable as a diagnostic.
    """
    pieces: list[list[tuple[float, float]]] = []
    for s in marks:
        if pieces and math.dist(pieces[-1][-1], s[0]) <= join_tol:
            pieces[-1].extend(s[1:])
        else:
            pieces.append(list(s))
    return pieces


def extract(sheet: Sheet, which: str = "NKDA") -> Ring:
    """Recover one boundary as a closed ring.

    For NKDA this is the whole boundary and is asserted to be a single drawn run. For
    PLANNING it is the largest drawn run, which is a diagnostic only.
    """
    style = NKDA if which.upper() == "NKDA" else PLANNING
    marks, dropped = boundary_marks(sheet, style)
    if not marks:
        raise RuntimeError(f"no {which} strokes found in layer {style['layer']}")
    pieces = chain_marks(marks)
    if which.upper() == "NKDA" and len(pieces) != 1:
        raise RuntimeError(f"NKDA boundary split into {len(pieces)} runs in stream order; "
                           "expected one continuous dashed run")
    pts = max(pieces, key=len)
    ring = Ring(points=pts, style=dict(style), n_marks=len(marks), n_dropped=dropped,
                n_pieces=len(pieces))
    ring.closure_gap_u = math.dist(pts[0], pts[-1])
    ring.perimeter_u = float(Polygon(pts).buffer(0).exterior.length)
    return ring


# ------------------------------------------------------------------------- scale

def solve_scale(sheet: Sheet) -> tuple[float, list[dict]]:
    """Metres per PDF unit from the NKDA ring and the statutory 29.34 km2.

    The PLANNING ring is measured too, purely as a diagnostic. It is deliberately not
    used to fix the scale: its published area is not cited anywhere we could verify, and
    the NKDA figure is the one with a statutory source.
    """
    rows = []
    for label, style, km2 in (("NKDA", NKDA, NKDA_OFFICIAL_KM2), ("PLANNING", PLANNING, None)):
        try:
            ring = extract(sheet, label)
        except RuntimeError as exc:
            rows.append({"boundary": label, "error": str(exc)})
            continue
        row = {"boundary": label, "measured_u2": ring.area_u2,
               "n_marks": ring.n_marks, "n_dropped": ring.n_dropped,
               "n_points": ring.n_points, "n_pieces": ring.n_pieces,
               "bbox_u": [round(v, 1) for v in ring.bounds[2:]],
               "closure_gap_u": round(ring.closure_gap_u, 2),
               "perimeter_u": round(ring.perimeter_u, 1)}
        if km2:
            row["official_km2"] = km2
            row["scale_m_per_unit"] = math.sqrt(km2 * 1e6 / ring.area_u2)
        rows.append(row)

    nkda = next((r for r in rows if r["boundary"] == "NKDA"), None)
    if not nkda or "scale_m_per_unit" not in nkda:
        raise RuntimeError("NKDA ring not recovered; cannot solve scale")
    return nkda["scale_m_per_unit"], rows


def scale_report(sheet: Sheet) -> str:
    scale, rows = solve_scale(sheet)
    lines = [f"scale solved from the statutory NKDA area: {scale:.4f} m per PDF unit", ""]
    lines.append(f"{'boundary':>10} {'marks':>6} {'dropped':>8} {'runs':>5} {'pts':>6} "
                 f"{'area u2':>14} {'closure':>8} {'perim u':>9} {'official':>9} {'m/unit':>8}")
    for r in rows:
        if "error" in r:
            lines.append(f"{r['boundary']:>10}  {r['error']}")
            continue
        off = f"{r['official_km2']:8.2f}k" if "official_km2" in r else f"{'-':>9}"
        sc = f"{r['scale_m_per_unit']:8.4f}" if "scale_m_per_unit" in r else f"{'-':>8}"
        lines.append(f"{r['boundary']:>10} {r['n_marks']:6d} {r['n_dropped']:8d} "
                     f"{r['n_pieces']:5d} {r['n_points']:6d} {r['measured_u2']:14,.0f} "
                     f"{r['closure_gap_u']:7.2f}u {r['perimeter_u']:9,.0f} {off} {sc}")
    lines += ["", "The PLANNING ring is a diagnostic only; its published area is not "
              "the source of the scale, and it is drawn as several separate runs."]
    return "\n".join(lines)


# ------------------------------------------------------------------ registration

@dataclass
class Similarity:
    """PDF user units -> EPSG:4326. Scale held fixed; rotation and translation solved.

        E = mpu * ( a*x - b*y ) + E0        (metres east of LON0)
        N = mpu * ( b*x + a*y ) + N0        (metres north of LAT0)
    """
    mpu: float
    a: float
    b: float
    e0: float
    n0: float

    def __call__(self, x: float, y: float) -> tuple[float, float]:
        e = self.mpu * (self.a * x - self.b * y) + self.e0
        n = self.mpu * (self.b * x + self.a * y) + self.n0
        return (LON0 + e / M_PER_DEG_LON, LAT0 + n / M_PER_DEG_LAT)

    def as_dict(self) -> dict:
        return {"mpu": self.mpu, "a": self.a, "b": self.b,
                "e0_m": self.e0, "n0_m": self.n0,
                "rotation_deg": round(math.degrees(math.atan2(self.b, self.a)), 4)}


def _gcp_arrays(mpu: float):
    names = list(GCP)
    P = np.array([GCP[n][0] for n in names], float)
    ll = np.array([GCP[n][1] for n in names], float)
    G = np.column_stack([(ll[:, 0] - LON0) * M_PER_DEG_LON,
                         (ll[:, 1] - LAT0) * M_PER_DEG_LAT])
    return names, P, G


def register(mpu: float = SCALE_M_PER_UNIT) -> tuple[Similarity, dict]:
    """Solve rotation and translation with the scale fixed at `mpu`.

    The sheet is rotated ~90 degrees, and label anchors carry drafter placement error,
    so rotation is found by a fine angular search rather than in closed form.
    """
    names, P, G = _gcp_arrays(mpu)
    best = None
    for deg in np.arange(0.0, 360.0, 0.02):
        th = math.radians(deg)
        c, s = math.cos(th), math.sin(th)
        R = np.array([[c, -s], [s, c]])
        A = mpu * (P @ R.T)
        t = G.mean(0) - A.mean(0)
        r = np.hypot(*(A + t - G).T)
        v = float((r ** 2).mean())
        if best is None or v < best[0]:
            best = (v, deg, R, t, r)
    v, deg, R, t, r = best
    sim = Similarity(mpu=mpu, a=float(R[0, 0]), b=float(R[1, 0]),
                     e0=float(t[0]), n0=float(t[1]))
    info = {
        "n_gcp": len(names),
        "rotation_deg": round(deg, 4),
        "rms_m": round(float(math.sqrt(v)), 1),
        "max_m": round(float(r.max()), 1),
        "residuals_m": {n: round(float(x), 1) for n, x in zip(names, r)},
        "rejected_gcp": dict(REJECTED_GCP),
    }
    return sim, info


def scale_probe(mpu_lo: float = 0.9, mpu_hi: float = 3.4) -> tuple[float, float]:
    """GCP residual RMS as a function of assumed scale.

    Independent of the area assumption: it asks which scale makes the OSM control points
    line up best. Weak, because label anchors are only good to a few hundred metres, but
    it does rule out scales far from the area-derived value.
    """
    out = []
    for mpu in np.arange(mpu_lo, mpu_hi, 0.02):
        sim, info = register(float(mpu))
        out.append((info["rms_m"], float(mpu)))
    return min(out)


def registration_report(mpu: float = SCALE_M_PER_UNIT) -> str:
    sim, info = register(mpu)
    probe_rms, probe_mpu = scale_probe()
    lines = [f"registration: scale fixed at {mpu:.4f} m/unit, rotation solved", ""]
    lines.append(f"{'gcp':>12} {'pdf x':>9} {'pdf y':>9} {'lon':>10} {'lat':>9} {'resid m':>9}")
    for n, ((px, py), (lon, lat)) in GCP.items():
        lines.append(f"{n:>12} {px:9.0f} {py:9.0f} {lon:10.5f} {lat:9.5f} "
                     f"{info['residuals_m'][n]:9.0f}")
    lines += ["", f"rotation = {info['rotation_deg']:.2f} deg",
              f"translation = ({sim.e0:,.0f} m E, {sim.n0:,.0f} m N) of ({LON0}, {LAT0})",
              f"RMS = {info['rms_m']:,.0f} m over {info['n_gcp']} points, max = {info['max_m']:,.0f} m",
              "", "rejected as control points:"]
    for n, why in REJECTED_GCP.items():
        lines.append(f"  {n}: {why}")
    lines += ["", "independent scale probe (GCP residuals only, no area used):",
              f"  optimum {probe_mpu:.2f} m/unit at RMS {probe_rms:,.0f} m; "
              f"area-derived {mpu:.4f} is {100 * (register(mpu)[1]['rms_m'] / probe_rms - 1):.0f}% above it"]
    return "\n".join(lines)


# ------------------------------------------------------------------------ export

def registered_ring(sheet: Sheet | None = None, mpu: float = SCALE_M_PER_UNIT):
    """The NKDA ring in EPSG:4326, plus the registration record."""
    sheet = sheet or load()
    ring = extract(sheet, "NKDA")
    sim, info = register(mpu)
    ring.registration = {"transform": sim, "info": info}
    coords = [[round(v, 7) for v in sim(x, y)] for x, y in ring.points]
    if coords[0] != coords[-1]:
        coords.append(coords[0])
    geom = {"type": "Polygon", "coordinates": [coords]}
    fc = {"type": "FeatureCollection",
          "features": [{"type": "Feature", "properties": {
              "name": "NKDA (New Town Kolkata Development Authority) area",
              "source": "digitised from nkdamar.org maps-of-new-town-planning-area.pdf",
              "statutory_km2": NKDA_OFFICIAL_KM2,
              "scale_m_per_unit": mpu,
              "rotation_deg": info["rotation_deg"],
              "registration_rms_m": info["rms_m"],
          }, "geometry": geom}]}
    return ring, fc, info


def area_km2(geom: dict) -> float:
    """Area of a GeoJSON geometry in km2, measured on the UTM 45N grid."""
    import pyproj
    g = shape(geom)
    if g.geom_type == "GeometryCollection":
        g = max(g.geoms, key=lambda p: p.area)
    tr = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:32645", always_xy=True)
    x, y = tr.transform(*zip(*g.exterior.coords))
    return Polygon(zip(x, y)).area / 1e6


def validate(fc: dict) -> dict:
    """Area check plus the inside/outside spot checks."""
    from shapely.geometry import Point
    g = shape(fc["features"][0]["geometry"])
    rep = {"area_km2": round(area_km2(fc["features"][0]["geometry"]), 3),
           "statutory_km2": NKDA_OFFICIAL_KM2,
           "inside": {}, "outside": {}}
    rep["area_error_pct"] = round(
        100 * (rep["area_km2"] - NKDA_OFFICIAL_KM2) / NKDA_OFFICIAL_KM2, 2)
    for n, (lat, lon) in MUST_BE_INSIDE.items():
        rep["inside"][n] = bool(g.contains(Point(lon, lat)))
    for n, (lat, lon) in MUST_BE_OUTSIDE.items():
        rep["outside"][n] = bool(g.contains(Point(lon, lat)))
    b = g.bounds
    rep["extent_km"] = [round((b[2] - b[0]) * M_PER_DEG_LON / 1000, 2),
                        round((b[3] - b[1]) * M_PER_DEG_LAT / 1000, 2)]
    return rep


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default="data/newtown_boundary.geojson")
    ap.add_argument("--report", action="store_true", help="print both reports")
    a = ap.parse_args(argv)

    sheet = load()
    scale, rows = solve_scale(sheet)
    ring, fc, info = registered_ring(sheet, scale)
    rep = validate(fc)

    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w") as fh:
        json.dump(fc, fh, separators=(",", ":"), ensure_ascii=False)
        fh.write("\n")

    if a.report:
        print(scale_report(sheet))
        print()
        print(registration_report(scale))
        print()
    print(f"wrote {a.out}")
    print(f"  scale {scale:.4f} m/unit, rotation {info['rotation_deg']:.2f} deg, "
          f"RMS {info['rms_m']:,.0f} m")
    print(f"  area {rep['area_km2']} km2 (statutory {NKDA_OFFICIAL_KM2}, "
          f"{rep['area_error_pct']:+.2f}%), extent {rep['extent_km'][0]} x {rep['extent_km'][1]} km")
    print(f"  must be inside : {rep['inside']}")
    print(f"  must be outside: {rep['outside']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())