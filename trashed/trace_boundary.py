"""Trace the two administrative boundaries off the NKDA plan-area sheet.

The sheet draws both boundaries as *dotted/cased* lines, i.e. hundreds of short
independent strokes rather than one path object:

* PLANNING AREA  - dark red (0.58, 0, 0), line width 25, ~2,838 dashes (layer 6)
* NKDA AREA     - blue (0, 0, 1), line width 19, ~7,953 dashes (layer 6)

So the boundaries are recovered by chaining dashes whose endpoints touch, then taking
the longest chain. That is why a naive scan for "one big ring" finds nothing: there isn't
one.

`trace()` returns the chained centreline; `centreline_area()` closes it and shoelaces it,
which is what fixes the drawing's scale against the official published areas.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from shapely.geometry import LineString, Polygon

import ntpa_boundary as N

PLANNING_AREA_STYLE = ((0.58, 0.0, 0.0), 25.0, 93.9)     # colour, line width, km2
NKDA_AREA_STYLE = ((0.0, 0.0, 1.0), 19.0, 29.34)
JOIN_TOL = 60.0          # PDF units; dashes are ~31 long with similar gaps


@dataclass
class Trace:
    points: list[tuple[float, float]]
    n_dashes: int
    style: tuple
    line_width: float

    @property
    def length(self) -> float:
        return sum(math.dist(self.points[i], self.points[i + 1])
                   for i in range(len(self.points) - 1))

    def polygon(self) -> Polygon:
        return Polygon(self.points)

    def centreline_area(self) -> float:
        return self.polygon().area


def _dashes(md, colour, width, layers) -> list[LineString]:
    out = []
    for li in layers:
        m = md.per_layer.get(li)
        if m is None:
            continue
        for r in m.rings:
            if r.stroke and tuple(round(c, 2) for c in r.stroke) == colour \
                    and abs(r.line_width - width) < 1.5 and len(r.points) >= 2:
                out.append(LineString(r.points))
    return out


def _components(segs: list[LineString], tol: float) -> list[list[int]]:
    """Union-find over segment endpoints; return groups of segment indices."""
    nodes = []
    for i, s in enumerate(segs):
        nodes.append((s.coords[0], i, 0))
        nodes.append((s.coords[-1], i, 1))
    parent = list(range(len(segs)))

    def find(a: int) -> int:
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    cell = tol
    grid: dict[tuple[int, int], list[int]] = {}
    for ni, (xy, _i, _e) in enumerate(nodes):
        key = (int(xy[0] // cell), int(xy[1] // cell))
        grid.setdefault(key, []).append(ni)
    for key, members in grid.items():
        cand = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                cand.extend(grid.get((key[0] + dx, key[1] + dy), ()))
        for ni in members:
            x1, y1 = nodes[ni][0]
            for nj in cand:
                if nj <= ni:
                    continue
                x2, y2 = nodes[nj][0]
                if math.dist((x1, y1), (x2, y2)) <= tol:
                    union(nodes[ni][1], nodes[nj][1])

    groups: dict[int, list[int]] = {}
    for i in range(len(segs)):
        groups.setdefault(find(i), []).append(i)
    return list(groups.values())


def _walk(segs: list[LineString], idxs: list[int]) -> list[tuple[float, float]]:
    """Greedily order a connected group of segments into one polyline."""
    remaining = {i: list(segs[i].coords) for i in idxs}
    ends = {}
    for i, cs in remaining.items():
        ends.setdefault(i, set()).update({cs[0], cs[-1]})

    start = min(idxs, key=lambda i: len(ends[i]))
    chain = list(remaining[start])
    del remaining[start]
    while remaining:
        tail = chain[-1]
        best, bestd, rev = None, None, False
        for i, cs in remaining.items():
            for pt, r in ((cs[0], False), (cs[-1], True)):
                d = math.dist(tail, pt)
                if bestd is None or d < bestd:
                    best, bestd, rev = i, d, r
        if best is None or bestd > JOIN_TOL:
            break
        cs = remaining.pop(best)
        chain.extend(reversed(cs) if rev else cs)
    return chain


def trace(md, colour, width, layers, official_km2: float | None = None) -> Trace:
    segs = _dashes(md, colour, width, layers)
    groups = _components(segs, JOIN_TOL)
    best_pts: list[tuple[float, float]] = []
    best_n = 0
    for g in groups:
        pts = _walk(segs, g)
        if len(pts) > len(best_pts):
            best_pts, best_n = pts, len(g)
    return Trace(points=best_pts, n_dashes=best_n, style=colour, line_width=width)


def load():
    return N.load_map(N.fetch_map("boundary/map.pdf"))


def trace_both(md) -> tuple[Trace, Trace]:
    planning = trace(md, *PLANNING_AREA_STYLE[:2], layers=(6,),
                     official_km2=PLANNING_AREA_STYLE[2])
    nkda = trace(md, *NKDA_AREA_STYLE[:2], layers=(5, 6),
                 official_km2=NKDA_AREA_STYLE[2])
    return planning, nkda