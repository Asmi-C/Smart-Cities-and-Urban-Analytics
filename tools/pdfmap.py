"""Minimal PDF content-stream parser for the official NKDA/NTPA plan-area map.

The map is a true vector drawing: ~6,400 filled polygons (mouza / land-use units) plus
labelled features, all inside a clip rectangle. There is no coordinate grid on the sheet,
so the drawing has to be georeferenced from named features (see extract_ntpa_boundary.py).

Only the subset of PDF operators this map actually uses is implemented.
"""
from __future__ import annotations

import re
import zlib
from dataclasses import dataclass, field

import requests

PDF_URL = "https://nkdamar.org/storage/files/maps-of-new-town-planning-area.pdf"
UA = {"User-Agent": "Mozilla/5.0 (research)"}

# token regex: numbers, strings, names, arrays, operators
_TOKEN = re.compile(
    rb"""
      (?P<num>[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)
    | (?P<str>\((?:\\.|[^\\()])*\))
    | (?P<name>/[^\s/\[\]()<>{}]*)
    | (?P<arr>[\[\]])
    | (?P<op>[A-Za-z][A-Za-z0-9*'"]*|[*'"])
    """,
    re.VERBOSE,
)

_ESCAPES = {b"n": b"\n", b"r": b"\r", b"t": b"\t", b"b": b"\b", b"f": b"\f",
            b"(": b"(", b")": b")", b"\\": b"\\"}


def pdf_unescape(raw: bytes) -> str:
    """Decode a PDF literal string body (without the enclosing parentheses)."""
    out = bytearray()
    i = 0
    while i < len(raw):
        ch = raw[i:i + 1]
        if ch == b"\\" and i + 1 < len(raw):
            nxt = raw[i + 1:i + 2]
            if nxt in _ESCAPES:
                out += _ESCAPES[nxt]
                i += 2
                continue
            if nxt.isdigit():                      # octal escape, up to 3 digits
                oct_digits = b""
                j = i + 1
                while j < len(raw) and len(oct_digits) < 3 and raw[j:j + 1].isdigit():
                    oct_digits += raw[j:j + 1]
                    j += 1
                out.append(int(oct_digits, 8) & 0xFF)
                i = j
                continue
            if nxt in (b"\n", b"\r"):              # line continuation
                i += 2
                continue
            out += nxt
            i += 2
            continue
        out += ch
        i += 1
    return out.decode("latin-1")


@dataclass
class Matrix:
    a: float = 1.0
    b: float = 0.0
    c: float = 0.0
    d: float = 1.0
    e: float = 0.0
    f: float = 0.0

    def apply(self, x: float, y: float) -> tuple[float, float]:
        return (self.a * x + self.c * y + self.e, self.b * x + self.d * y + self.f)

    def mul(self, o: "Matrix") -> "Matrix":
        return Matrix(
            self.a * o.a + self.b * o.c, self.a * o.b + self.b * o.d,
            self.c * o.a + self.d * o.c, self.c * o.b + self.d * o.d,
            self.e * o.a + self.f * o.c + o.e, self.e * o.b + self.f * o.d + o.f,
        )


@dataclass
class Ring:
    points: list[tuple[float, float]]
    fill: tuple[float, float, float] | None = None
    stroke: tuple[float, float, float] | None = None
    line_width: float = 0.0
    source: str = "fill"          # "fill" | "stroke"

    @property
    def area(self) -> float:
        """Absolute shoelace area in PDF units squared."""
        pts = self.points
        if len(pts) < 3:
            return 0.0
        s = 0.0
        for i in range(len(pts)):
            x0, y0 = pts[i]
            x1, y1 = pts[(i + 1) % len(pts)]
            s += x0 * y1 - x1 * y0
        return abs(s) / 2.0

    @property
    def perimeter(self) -> float:
        pts = self.points
        return sum(
            ((pts[(i + 1) % len(pts)][0] - pts[i][0]) ** 2
             + (pts[(i + 1) % len(pts)][1] - pts[i][1]) ** 2) ** 0.5
            for i in range(len(pts))
        )


@dataclass
class Label:
    text: str
    x: float
    y: float
    angle_deg: float
    font_size: float
    font: str = ""


@dataclass
class MapContent:
    width: float = 0.0
    height: float = 0.0
    rings: list[Ring] = field(default_factory=list)
    labels: list[Label] = field(default_factory=list)
    clip: list[tuple[float, float, float, float]] = field(default_factory=list)


def fetch_map_bytes(url: str = PDF_URL, path: str | None = None) -> bytes:
    if path:
        return open(path, "rb").read()
    r = requests.get(url, headers=UA, timeout=180)
    r.raise_for_status()
    return r.content


def largest_content_stream(pdf: bytes) -> tuple[bytes, float, float]:
    """Return (inflated largest stream, page width, page height)."""
    m = re.search(rb"/MediaBox\s*\[\s*([\d.+-]+)\s+([\d.+-]+)\s+([\d.+-]+)\s+([\d.+-]+)", pdf)
    width = height = 0.0
    if m:
        width = float(m.group(3)) - float(m.group(1))
        height = float(m.group(4)) - float(m.group(2))
    best = b""
    for sm in re.finditer(rb"stream\r?\n(.*?)endstream", pdf, re.S):
        try:
            d = zlib.decompress(sm.group(1))
        except Exception:
            continue
        if len(d) > len(best):
            best = d
    return best, width, height


def parse(stream: bytes, width: float = 0.0, height: float = 0.0) -> MapContent:
    """Parse a content stream into filled/stroked rings and positioned text."""
    out = MapContent(width=width, height=height)

    ctm = Matrix()
    stack: list[Matrix] = []
    fill = stroke = None
    line_width = 0.0
    cur: list[tuple[float, float]] = []
    start_pt: tuple[float, float] | None = None
    cursor = (0.0, 0.0)

    # text state
    in_text = False
    tm = tlm = Matrix()
    font_size = 0.0
    font_name = ""
    pending: list[float] = []

    def flush(paint_fill: bool, paint_stroke: bool) -> None:
        nonlocal cur
        if len(cur) >= 2 and (paint_fill or paint_stroke):
            out.rings.append(Ring(
                points=list(cur),
                fill=fill if paint_fill else None,
                stroke=stroke if paint_stroke else None,
                line_width=line_width,
                source="fill" if paint_fill else "stroke",
            ))
        cur = []

    for m in _TOKEN.finditer(stream):
        kind = m.lastgroup
        tok = m.group()
        if kind == "num":
            pending.append(float(tok))
            continue
        if kind == "str":
            pending.append(pdf_unescape(tok[1:-1]))   # type: ignore[arg-type]
            continue
        if kind == "name":
            pending.append(tok.decode("latin-1"))
            continue
        if kind == "arr":
            pending.append(tok.decode("latin-1"))
            continue

        op = tok.decode("latin-1")
        nums = [p for p in pending if isinstance(p, float)]
        strings = [p for p in pending if isinstance(p, str)]

        if op == "q":
            stack.append(Matrix(ctm.a, ctm.b, ctm.c, ctm.d, ctm.e, ctm.f))
        elif op == "Q":
            if stack:
                ctm = stack.pop()
        elif op == "cm" and len(nums) >= 6:
            ctm = ctm.mul(Matrix(*nums[-6:]))
        elif op in ("rg", "sc", "scn") and len(nums) >= 3:
            fill = tuple(nums[-3:])
        elif op == "g" and nums:
            fill = (nums[-1],) * 3
        elif op in ("RG", "SC", "SCN") and len(nums) >= 3:
            stroke = tuple(nums[-3:])
        elif op == "G" and nums:
            stroke = (nums[-1],) * 3
        elif op == "w" and nums:
            line_width = nums[-1]
        elif op == "m" and len(nums) >= 2:
            if len(cur) >= 2:
                flush(False, True)          # implicit stroke of the open subpath
            cursor = ctm.apply(nums[-2], nums[-1])
            start_pt = cursor
            cur = [cursor]
        elif op == "l" and len(nums) >= 2:
            cursor = ctm.apply(nums[-2], nums[-1])
            cur.append(cursor)
        elif op == "c" and len(nums) >= 6:
            p1 = ctm.apply(nums[-6], nums[-5])
            p2 = ctm.apply(nums[-4], nums[-3])
            p3 = ctm.apply(nums[-2], nums[-1])
            cur.extend(_bezier(cur[-1] if cur else p1, p1, p2, p3))
            cursor = p3
        elif op in ("v", "y") and len(nums) >= 4:
            p2 = ctm.apply(nums[-4], nums[-3])
            p3 = ctm.apply(nums[-2], nums[-1])
            cur.extend(_bezier(cur[-1] if cur else p2, p2, p2, p3))
            cursor = p3
        elif op == "re" and len(nums) >= 4:
            x, y, w, h = nums[-4:]
            pts = [ctm.apply(x, y), ctm.apply(x + w, y),
                   ctm.apply(x + w, y + h), ctm.apply(x, y + h)]
            flush(False, False)
            cur = pts + [pts[0]]
        elif op == "h":
            if cur and start_pt is not None and cur[-1] != start_pt:
                cur.append(start_pt)
        elif op in ("S", "s"):
            flush(False, True)
        elif op in ("f", "F", "f*"):
            flush(True, False)
        elif op in ("B", "B*"):
            flush(True, True)
        elif op in ("b", "b*"):
            if cur and start_pt is not None and cur[-1] != start_pt:
                cur.append(start_pt)
            flush(True, True)
        elif op == "n":
            flush(False, False)
        elif op == "W" or op == "W*":
            pass
        # ---- text ----
        elif op == "BT":
            in_text = True
            tm = tlm = Matrix()
        elif op == "ET":
            in_text = False
        elif op == "Tf" and nums:
            font_size = nums[-1]
            font_name = next((s for s in strings if s.startswith("/")), font_name)
        elif op == "Tm" and len(nums) >= 6:
            tm = tlm = Matrix(*nums[-6:])
        elif op in ("Td", "TD") and len(nums) >= 2:
            tlm = tlm.mul(Matrix(1, 0, 0, 1, nums[-2], nums[-1]))
            tm = tlm
        elif op == "T*":
            tlm = tlm.mul(Matrix(1, 0, 0, 1, 0, -font_size))
            tm = tlm
        elif op == "Tj" and strings:
            gx, gy = ctm.apply(tm.e, tm.f)
            out.labels.append(Label(strings[-1], gx, gy,
                                    _angle_deg(tm), font_size, font_name))
        elif op == "TJ":
            pass
        pending = []

    flush(False, False)
    return out


def _bezier(p0, p1, p2, p3, n: int = 12) -> list[tuple[float, float]]:
    pts = []
    for i in range(1, n + 1):
        t = i / n
        u = 1 - t
        pts.append((
            u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
            u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1],
        ))
    return pts


def _angle_deg(m: Matrix) -> float:
    import math
    return math.degrees(math.atan2(m.b, m.a))