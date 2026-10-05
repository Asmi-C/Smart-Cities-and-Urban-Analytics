"""Extract the authoritative mouza schedule from the LUDCP 2012 PDF.

The Land Use & Development Control Plan for New Town Planning Area 2012
(wbhidcoltd.com/upload_file/report_publication/report11.pdf) contains Table 2: the
schedule of 45 mouzas, each with its J.L. (Jote/Lot) number and area in km²,
summing to 60.354 km². Those J.L. numbers are the keys that let us identify the
same mouzas on the NKDA plan-area map and lock the drawing's scale.

The PDF uses subset fonts, so text has to be decoded through each font's
ToUnicode CMap rather than read as raw bytes.
"""
from __future__ import annotations

import re
import zlib
from dataclasses import dataclass

import requests

LUDCP_URL = "https://www.wbhidcoltd.com/upload_file/report_publication/report11.pdf"
UA = {"User-Agent": "Mozilla/5.0 (research)"}

_OBJ = re.compile(rb"(\d+)\s+(\d+)\s+obj\b(.*?)\bendobj", re.S)
_STREAM = re.compile(rb"stream\r?\n(.*?)\r?\nendstream", re.S)
_TOKEN = re.compile(
    rb"""
      (?P<num>[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)
    | (?P<str>\((?:\\.|[^\\()])*\))
    | (?P<name>/[^\s/\[\]()<>{}]*)
    | (?P<op>[A-Za-z][A-Za-z0-9*'"]*|[*'"])
    """,
    re.VERBOSE,
)
_ESCAPES = {b"n": b"\n", b"r": b"\r", b"t": b"\t", b"b": b"\b", b"f": b"\f",
            b"(": b"(", b")": b")", b"\\": b"\\"}


def unescape(raw: bytes) -> bytes:
    out = bytearray()
    i = 0
    while i < len(raw):
        ch = raw[i:i + 1]
        if ch == b"\\" and i + 1 < len(raw):
            nxt = raw[i + 1:i + 2]
            if nxt.isdigit():
                digits = b""
                j = i + 1
                while j < len(raw) and len(digits) < 3 and raw[j:j + 1].isdigit():
                    digits += raw[j:j + 1]
                    j += 1
                out.append(int(digits, 8) & 0xFF)
                i = j
                continue
            out += _ESCAPES.get(nxt, nxt)
            i += 2
            continue
        out += ch
        i += 1
    return bytes(out)


@dataclass
class TextItem:
    stream: int
    x: float
    y: float
    size: float
    text: str


def _objects(pdf: bytes) -> dict[int, bytes]:
    return {int(m.group(1)): m.group(3) for m in _OBJ.finditer(pdf)}


def _stream_of(body: bytes) -> bytes | None:
    m = _STREAM.search(body)
    if not m:
        return None
    try:
        return zlib.decompress(m.group(1))
    except Exception:
        return m.group(1)


def build_cmaps(objs: dict[int, bytes]) -> dict[int, dict[int, str]]:
    """font object number -> {glyph code -> unicode string}"""
    out: dict[int, dict[int, str]] = {}
    for num, body in objs.items():
        ref = re.search(rb"/ToUnicode\s+(\d+)\s+\d+\s+R", body)
        if not ref:
            continue
        cm = _stream_of(objs.get(int(ref.group(1)), b""))
        if not cm:
            continue
        table: dict[int, str] = {}
        for blk in re.findall(rb"beginbfchar(.*?)endbfchar", cm, re.S):
            for src, dst in re.findall(rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", blk):
                table[int(src, 16)] = "".join(
                    chr(int(dst[i:i + 4], 16)) for i in range(0, len(dst), 4))
        for blk in re.findall(rb"beginbfrange(.*?)endbfrange", cm, re.S):
            for lo, hi, dst in re.findall(
                    rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", blk):
                lo_i, hi_i, base = int(lo, 16), int(hi, 16), int(dst, 16)
                for k in range(lo_i, min(hi_i, lo_i + 2048) + 1):
                    table[k] = chr(base + k - lo_i)
        if table:
            out[num] = table
    return out


def extract_text_items(pdf: bytes) -> list[TextItem]:
    objs = _objects(pdf)
    cmaps = build_cmaps(objs)

    page_refs: list[int] = []
    for num, body in sorted(objs.items()):
        if re.search(rb"/Type\s*/Page(?![s])", body):
            page_refs.append(num)
    if not page_refs:
        page_refs = sorted(objs)

    items: list[TextItem] = []
    for pi, pref in enumerate(page_refs):
        body = objs.get(pref, b"")
        # font resource map for this page
        fontmap: dict[str, int] = {}
        res = re.search(rb"/Font\s*<<(.*?)>>", body, re.S)
        if res:
            for nm, on in re.findall(rb"/([A-Za-z0-9_]+)\s+(\d+)\s+\d+\s+R", res.group(1)):
                fontmap[nm] = int(on)
        cm = re.search(rb"/Contents\s*(?:(\d+)\s+\d+\s+R|\[(.*?)\])", body, re.S)
        if not cm:
            continue
        refs = ([int(cm.group(1))] if cm.group(1)
                else [int(x) for x in re.findall(rb"(\d+)\s+\d+\s+R", cm.group(2))])
        content = b""
        for r in refs:
            content += (_stream_of(objs.get(r, b"")) or b"") + b"\n"
        if not content:
            continue

        cur_cmap: dict[int, str] | None = None
        size = 0.0
        tm = [1, 0, 0, 1, 0, 0]
        pending: list = []
        for m in _TOKEN.finditer(content):
            kind = m.lastgroup
            tok = m.group()
            if kind == "num":
                pending.append(float(tok))
                continue
            if kind == "str":
                pending.append(unescape(tok[1:-1]))
                continue
            if kind == "name":
                pending.append(tok[1:].decode("latin-1"))
                continue
            op = tok.decode("latin-1")
            if op == "Tf" and pending:
                size = next((p for p in pending if isinstance(p, float)), 0.0)
                nm = next((p for p in pending if isinstance(p, str)), None)
                cur_cmap = cmaps.get(fontmap.get(nm, -1)) if nm else None
            elif op == "Tm" and len(pending) >= 6:
                nums = [p for p in pending if isinstance(p, float)]
                if len(nums) >= 6:
                    tm = nums[-6:]
            elif op == "Td" and len(pending) >= 2:
                nums = [p for p in pending if isinstance(p, float)]
                if len(nums) >= 2:
                    tm = tm[:4] + [tm[4] + nums[-2], tm[5] + nums[-1]]
            elif op == "Tj":
                raw = next((p for p in pending if isinstance(p, bytes)), None)
                if raw is not None:
                    if cur_cmap:
                        txt = "".join(
                            cur_cmap.get(int.from_bytes(raw[i:i + 2], "big"), "")
                            for i in range(0, len(raw) - 1, 2))
                    else:
                        txt = raw.decode("latin-1")
                    if txt.strip():
                        items.append(TextItem(pi, tm[4], tm[5], size, txt))
            pending = []
    return items


def fetch(url: str = LUDCP_URL, path: str | None = None) -> bytes:
    if path:
        return open(path, "rb").read()
    r = requests.get(url, headers=UA, timeout=300)
    r.raise_for_status()
    return r.content


# ---- Table 2 parsing -------------------------------------------------------

AREA = re.compile(r"^\d+\.\d{2,3}$")
JLTXT = re.compile(r"^\(?Full\)?$|^Full$")


def parse_table2(items: list[TextItem]) -> list[dict]:
    """Reconstruct Table 2 rows: serial, name, J.L. number, area."""
    page = next((it.stream for it in items
                 if "Schedule" in it.text and "mouza" in it.text.lower()), None)
    if page is None:
        return []
    rows = [it for it in items if it.stream in (page, page + 1, page + 2)]

    # keep items in reading order
    rows.sort(key=lambda it: (-round(it.y / 4), it.x))

    # group into visual rows
    lines: list[list[TextItem]] = []
    for it in rows:
        if lines and abs(lines[-1][0].y - it.y) < 3.0:
            lines[-1].append(it)
        else:
            lines.append([it])
    out: list[dict] = []
    for ln in lines:
        ln.sort(key=lambda it: it.x)
        texts = [it.text for it in ln]
        serial = texts[0] if re.fullmatch(r"\d{1,2}\.", texts[0]) else None
        areas = [t for t in texts if AREA.match(t)]
        jls = [t for t in texts if re.fullmatch(r"\d{1,3}", t)
               and not AREA.match(t) and serial is not None
               and texts.index(t) != 0]
        if not areas or serial is None:
            continue
        name = ""
        jl = ""
        for t in texts[1:]:
            if AREA.match(t):
                continue
            if re.fullmatch(r"\d{1,3}", t) and not jl:
                jl = t
            elif not JLTXT.match(t):
                name += t
        out.append({"serial": int(serial.rstrip(".")), "name": name.strip(),
                    "jl": jl, "area": float(areas[-1])})
    return out