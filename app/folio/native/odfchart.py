"""A chart in an OpenDocument file, read into Page's own chart model (charts.py), so an .odt's
charts come in as charts that can be edited, not as nothing (W5-04).

An .odt keeps each chart as a small document of its own ("Object 1/content.xml"): a chart:chart
element saying what kind it is, its series as cell ranges, and the table those ranges point into.
Its only picture is a StarView metafile, which nothing outside LibreOffice can draw, so the chart
is rebuilt from its data instead."""
import re
import xml.etree.ElementTree as ET

NS = {
    "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
    "style": "urn:oasis:names:tc:opendocument:xmlns:style:1.0",
    "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
    "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
    "chart": "urn:oasis:names:tc:opendocument:xmlns:chart:1.0",
    "svg": "urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0",
}


def _q(tag):
    p, _, n = tag.partition(":")
    return "{%s}%s" % (NS[p], n)


def _a(el, name, default=None):
    return el.get(_q(name), default) if el is not None else default


def _text(el):
    """The words of an element, paragraphs joined by spaces."""
    if el is None:
        return ""
    return " ".join(" ".join(t.strip() for t in p.itertext() if t.strip())
                    for p in el.iter(_q("text:p"))).strip()


def _col_index(letters):
    n = 0
    for ch in letters.upper():
        n = n * 26 + (ord(ch) - 64)
    return n - 1


_CELL = re.compile(r"\$?([A-Za-z]+)\$?(\d+)")


def _range(addr):
    """'local-table.$B$2:.$B$5' (or 'Sheet1.B2:Sheet1.B5', or a single cell) as
    ((col0, row0), (col1, row1)), zero-based; None if it can't be read."""
    if not addr:
        return None
    addr = addr.split(" ")[0]          # several ranges: the first is the one that matters here
    cells = []
    for part in addr.split(":"):
        part = part.rsplit(".", 1)[-1]
        m = _CELL.fullmatch(part.strip())
        if not m:
            return None
        cells.append((_col_index(m.group(1)), int(m.group(2)) - 1))
    if len(cells) == 1:
        cells.append(cells[0])
    (c0, r0), (c1, r1) = cells[0], cells[1]
    return (min(c0, c1), min(r0, r1)), (max(c0, c1), max(r0, r1))


def _grid(table):
    """The chart's own data table as rows of cell values (number, text or None)."""
    rows = []
    for row in table.iter(_q("table:table-row")):
        cells = []
        for cell in row:
            if cell.tag not in (_q("table:table-cell"), _q("table:covered-table-cell")):
                continue
            rep = int(_a(cell, "table:number-columns-repeated", "1") or 1)
            vt = _a(cell, "office:value-type")
            if vt in ("float", "percentage", "currency"):
                try:
                    v = float(_a(cell, "office:value"))
                except (TypeError, ValueError):
                    v = None
            else:
                v = _text(cell) or None
            cells.extend([v] * min(rep, 1000))
        reps = int(_a(row, "table:number-rows-repeated", "1") or 1)
        rows.extend([cells] * min(reps, 1000))
    return rows


def _cells(grid, rng):
    """The values a range covers, in reading order."""
    if rng is None:
        return []
    (c0, r0), (c1, r1) = rng
    out = []
    for r in range(r0, r1 + 1):
        row = grid[r] if r < len(grid) else []
        for c in range(c0, c1 + 1):
            out.append(row[c] if c < len(row) else None)
    return out


def _props(root, name):
    """The chart:chart-properties of a named automatic style, as a dict of local names."""
    if not name:
        return {}
    for st in root.iter(_q("style:style")):
        if _a(st, "style:name") == name:
            p = st.find(_q("style:chart-properties"))
            if p is not None:
                return {k.split("}")[-1]: v for k, v in p.attrib.items()}
    return {}


def _num(v):
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(str(v).replace(",", "."))
    except (TypeError, ValueError):
        return 0.0


def read(content):
    """content: the bytes of an object's content.xml. Returns a chart model, or None when it
    isn't a chart (a formula or a drawing made in another program)."""
    try:
        root = ET.fromstring(content)
    except ET.ParseError:
        return None
    ch = root.find(".//" + _q("chart:chart"))
    if ch is None:
        return None
    kind = (_a(ch, "chart:class", "chart:bar") or "").split(":")[-1]
    pa = ch.find(_q("chart:plot-area"))
    if pa is None:
        return None
    pp = _props(root, _a(pa, "chart:style-name"))
    vertical = pp.get("vertical") == "true"
    stacked = pp.get("stacked") == "true"
    percent = pp.get("percentage") == "true"
    table = ch.find(".//" + _q("table:table"))
    grid = _grid(table) if table is not None else []

    series = []
    for s in pa.findall(_q("chart:series")):
        vals = _cells(grid, _range(_a(s, "chart:values-cell-range-address")))
        label = _cells(grid, _range(_a(s, "chart:label-cell-address")))
        sk = (_a(s, "chart:class") or "chart:" + kind).split(":")[-1]
        sp = _props(root, _a(s, "chart:style-name"))
        # a scatter series' x values are its first chart:domain
        dom = s.find(_q("chart:domain"))
        xs = _cells(grid, _range(_a(dom, "table:cell-range-address"))) if dom is not None else []
        name = next((str(x) for x in label if x not in (None, "")), "Series %d" % (len(series) + 1))
        series.append({"name": name, "vals": vals, "kind": sk, "xs": xs, "symbols": sp.get("symbol-type")})
    if not series:
        return None

    cats = []
    for ax in pa.findall(_q("chart:axis")):
        if _a(ax, "chart:dimension") == "x":
            c = ax.find(_q("chart:categories"))
            if c is not None:
                cats = [("" if v is None else ("%g" % v if isinstance(v, float) else str(v)))
                        for v in _cells(grid, _range(_a(c, "table:cell-range-address")))]
    if kind == "scatter" and not cats and series[0]["xs"]:
        cats = ["%g" % _num(v) for v in series[0]["xs"]]

    from . import charts
    m = charts.default_model()
    # the kind, in the order of Page's chart types
    lines = sum(1 for s in series if s["kind"] == "line")
    if kind == "bar" and lines and lines < len(series):
        t = 13                                           # columns with a line over them
    elif kind == "bar":
        t = (10 if stacked else 2) if vertical else (9 if percent else 1 if stacked else 0)
    elif kind == "line":
        marks = any((s["symbols"] or "automatic") != "none" for s in series)
        t = 4 if marks else 3
    elif kind == "area":
        t = 11 if stacked or percent else 7
    elif kind == "circle":
        t = 5
    elif kind == "ring":
        t = 6
    elif kind == "scatter":
        t = 8
    elif kind in ("radar", "filled-radar", "net"):
        t = 12
    else:
        t = 0
    m["type"] = t

    n = max(len(s["vals"]) for s in series)
    m["data"] = {
        "rows": [(cats[i] if i < len(cats) and cats[i] else "Category %d" % (i + 1)) for i in range(n)],
        "cols": [s["name"] for s in series],
        "values": [[_num(s["vals"][i]) if i < len(s["vals"]) and s["vals"][i] is not None else 0.0
                    for s in series] for i in range(n)],
    }
    title = ch.find(_q("chart:title"))
    m["title"] = _text(title) or None
    lg = ch.find(_q("chart:legend"))
    if lg is None:
        m["legend"] = "none"
    else:
        pos = _a(lg, "chart:legend-position", "end")
        m["legend"] = {"start": "left", "end": "right", "top": "top", "bottom": "bottom",
                       "top-start": "left", "bottom-start": "left", "top-end": "right",
                       "bottom-end": "right"}.get(pos, "right")
    for ax in pa.findall(_q("chart:axis")):
        at = ax.find(_q("chart:title"))
        if at is None:
            continue
        if _a(ax, "chart:dimension") == "x":
            m["x_title"] = _text(at) or None
        elif _a(ax, "chart:dimension") == "y":
            m["y_title"] = _text(at) or None
    # gridlines: [across (from the value axis), down (from the category axis), and their minor ones]
    g = [False, False, False, False]
    for ax in pa.findall(_q("chart:axis")):
        dim = _a(ax, "chart:dimension")
        if dim not in ("x", "y"):
            continue
        for gr in ax.findall(_q("chart:grid")):
            k = (0 if dim == "y" else 1) + (2 if _a(gr, "chart:class", "major") == "minor" else 0)
            g[k] = True
    if t in (2, 10):
        g = [g[1], g[0], g[3], g[2]]     # bars run across: the value axis is the horizontal one
    m["grid"] = g
    return m
