"""Table Layout tab: cell size, alignment grid, text direction, cell margins,
sort, repeat header rows, convert to text, formulas, AutoFit."""
import re

from gi.repository import Gtk

from . import docapi
from .widgets import FDialog, LengthSpin, combo, grid, heading


def current(m):
    vc = docapi.read_cursor(m)
    try:
        return vc.TextTable, vc.Cell
    except Exception:
        return None, None


def _rc(name):
    """'B3' -> (row 2, col 1). Nested names ('A1.1.1') use the outer part."""
    mm = re.match(r"([A-Za-z]+)(\d+)", name)
    letters, num = mm.group(1), int(mm.group(2))
    col = 0
    for ch in letters.upper():
        col = col * 26 + (ord(ch) - 64)
    return num - 1, col - 1


def _name(row, col):
    s = ""
    col += 1
    while col:
        col, rem = divmod(col - 1, 26)
        s = chr(65 + rem) + s
    return "%s%d" % (s, row + 1)


def _selected_cells(m, t):
    """Names of the selected cells (or the cell with the cursor)."""
    try:
        sel = docapi.controller(m).getSelection()
        names = getattr(sel, "CellRangeName", None) if hasattr(sel, "CellRangeName") else None
    except Exception:
        names = None
    vc = docapi.read_cursor(m)
    try:
        sel = docapi.controller(m).getSelection()
        rn = sel.getRangeName() if hasattr(sel, "getRangeName") else None
    except Exception:
        rn = None
    try:
        if rn and ":" in rn:
            c1, c2 = rn.split(":")
        else:
            rng = vc.getStart()
            c1 = rng.Cell.CellName
            c2 = vc.getEnd().Cell.CellName
    except Exception:
        try:
            c1 = c2 = vc.Cell.CellName
        except Exception:
            return []
    r1, k1 = _rc(c1)
    r2, k2 = _rc(c2)
    out = []
    for r in range(min(r1, r2), max(r1, r2) + 1):
        for k in range(min(k1, k2), max(k1, k2) + 1):
            out.append(_name(r, k))
    return [n for n in out if n in t.getCellNames()] or [c1]


# ------------------------------------------------------------ size
def _table_width(m, t):
    """The table's real width (a full-width table reports a bogus Width)."""
    if t.HoriOrient == 6:
        ps = docapi.page_setup(m)
        return ps["width"] - ps["left"] - ps["right"] - t.LeftMargin - t.RightMargin
    return t.Width


def cell_size(m):
    t, cell = current(m)
    if t is None:
        return None
    r, c = _rc(cell.CellName)
    row = t.getRows().getByIndex(r)
    seps = list(t.TableColumnSeparators or ())
    width = _table_width(m, t)
    rel = t.TableColumnRelativeSum or 10000
    pos = [0] + [s.Position for s in seps] + [rel]
    c = min(c, len(pos) - 2)
    col_w = int((pos[c + 1] - pos[c]) * width / rel)
    h = row.Height
    if row.IsAutoHeight and h < 300:
        # automatic height: show what one line of text takes
        try:
            pt = cell.createTextCursor().CharHeight or 11
        except Exception:
            pt = 11
        h = int(pt * 1.22 * 2540 / 72) + cell.TopBorderDistance + cell.BottomBorderDistance
    return h, col_w


def set_row_height(m, h):
    t, cell = current(m)
    if t is None:
        return
    rows = {_rc(n)[0] for n in _selected_cells(m, t)}
    for r in rows:
        row = t.getRows().getByIndex(r)
        row.IsAutoHeight = False
        row.Height = int(h)


def set_col_width(m, w):
    t, cell = current(m)
    if t is None:
        return
    _r, c = _rc(cell.CellName)
    seps = list(t.TableColumnSeparators or ())
    if not seps:
        return
    rel = t.TableColumnRelativeSum or 10000
    width = _table_width(m, t)
    pos = [0] + [s.Position for s in seps] + [rel]
    if c >= len(pos) - 1:
        return
    new = int(w * rel / width)
    delta = new - (pos[c + 1] - pos[c])
    if c < len(seps):
        # move this column's right edge; the next column absorbs the change
        lo = pos[c] + 50
        hi = pos[c + 2] - 50 if c + 2 < len(pos) else rel - 50
        seps[c].Position = max(lo, min(hi, seps[c].Position + delta))
    else:
        seps[c - 1].Position = max(pos[c - 1] + 50, seps[c - 1].Position - delta)
    t.TableColumnSeparators = tuple(seps)


def autofit(m, how):
    """'contents' / 'window' / 'fixed'."""
    t, _c = current(m)
    if t is None:
        return
    if how == "window":
        t.HoriOrient = 6         # FULL: as wide as the text area
    elif how == "fixed":
        w = t.Width
        t.HoriOrient = 0         # NONE
        t.Width = w
    return how == "contents"     # caller runs the engine's optimal width


# ------------------------------------------------------------ alignment


def text_direction(m):
    """Cycle horizontal -> rotated down -> rotated up."""
    t, cell = current(m)
    if t is None:
        return
    order = [0, 2, 5]       # LR_TB, TB_RL, BT_LR
    try:
        cur = cell.WritingMode
    except Exception:
        cur = 0
    nxt = order[(order.index(cur) + 1) % 3] if cur in order else 2
    for n in _selected_cells(m, t):
        try:
            t.getCellByName(n).WritingMode = nxt
        except Exception as e:
            print("text direction:", e)


def cell_margins(m):
    t, cell = current(m)
    if t is None:
        return None
    return (cell.TopBorderDistance, cell.BottomBorderDistance, cell.LeftBorderDistance,
            cell.RightBorderDistance)


def set_cell_margins(m, top, bottom, left, right):
    t, _c = current(m)
    if t is None:
        return
    for n in t.getCellNames():
        c = t.getCellByName(n)
        c.TopBorderDistance = int(top)
        c.BottomBorderDistance = int(bottom)
        c.LeftBorderDistance = int(left)
        c.RightBorderDistance = int(right)


# ------------------------------------------------------------ data
def repeat_header(m):
    t, _c = current(m)
    if t is None:
        return False
    on = not t.RepeatHeadline
    t.RepeatHeadline = on
    try:
        t.HeaderRowCount = 1 if on else 0
    except Exception:
        pass
    return on


def is_repeat_header(m):
    t, _c = current(m)
    return bool(t is not None and t.RepeatHeadline)


def table_text(t):
    rows = t.getRows().getCount()
    cols = t.getColumns().getCount()
    out = []
    for r in range(rows):
        row = []
        for c in range(cols):
            n = _name(r, c)
            row.append(t.getCellByName(n).getString() if n in t.getCellNames() else "")
        out.append(row)
    return out




FUNCS = ("SUM", "AVERAGE", "COUNT", "MAX", "MIN", "PRODUCT")


def default_formula(m):
    """=SUM(ABOVE) if there are numbers above, else =SUM(LEFT), like the original."""
    t, cell = current(m)
    if t is None:
        return "=SUM(ABOVE)"
    r, c = _rc(cell.CellName)
    for rr in range(r):
        n = _name(rr, c)
        if n in t.getCellNames() and _num(t.getCellByName(n).getString()) is not None:
            return "=SUM(ABOVE)"
    return "=SUM(LEFT)"


def _num(s):
    try:
        return float(s.replace(",", "").replace("$", "").replace("€", "").strip())
    except ValueError:
        return None


def insert_formula(m, formula):
    """=FUNC(ABOVE|LEFT|BELOW|RIGHT) or =FUNC(A1:B3) -> a live table formula."""
    t, cell = current(m)
    if t is None:
        return False
    f = formula.strip().lstrip("=")
    mm = re.match(r"(\w+)\s*\(\s*([^)]*)\)", f)
    if not mm:
        cell.setFormula(f)
        return True
    fn, arg = mm.group(1).upper(), mm.group(2).strip().upper()
    r, c = _rc(cell.CellName)
    rows = t.getRows().getCount()
    cols = t.getColumns().getCount()
    if arg == "ABOVE":
        rng = "%s:%s" % (_name(0, c), _name(r - 1, c)) if r else None
    elif arg == "BELOW":
        rng = "%s:%s" % (_name(r + 1, c), _name(rows - 1, c)) if r < rows - 1 else None
    elif arg == "LEFT":
        rng = "%s:%s" % (_name(r, 0), _name(r, c - 1)) if c else None
    elif arg == "RIGHT":
        rng = "%s:%s" % (_name(r, c + 1), _name(r, cols - 1)) if c < cols - 1 else None
    else:
        rng = arg
    if not rng:
        return False
    engine_fn = {"SUM": "sum", "AVERAGE": "mean", "COUNT": "count", "MAX": "max",
                 "MIN": "min", "PRODUCT": "product"}.get(fn, "sum")
    cell.setFormula("%s <%s>" % (engine_fn, rng))
    return True


# ------------------------------------------------------------ dialogs




def cell_margins_dialog(win):
    m = win.engine.model
    cur = cell_margins(m) if m else None
    if cur is None:
        return
    d = FDialog(win, "Table Options")
    spins = [LengthSpin(v, 0, 25400) for v in cur]
    d.add(heading("Default cell margins"))
    d.add(grid([["_Top:", spins[0], "_Left:", spins[2]],
                ["_Bottom:", spins[1], "_Right:", spins[3]]]))
    if d.ask() == Gtk.ResponseType.OK:
        vals = [s.mm100 for s in spins]
        win.engine.sync(lambda: set_cell_margins(m, *vals))
    d.done()
