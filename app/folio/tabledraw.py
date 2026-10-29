"""Draw Table and Eraser (Table Layout > Draw), the Insert Cells dialog and
the full Table Properties dialog."""
import math

from gi.repository import Gdk, GLib, Gtk

from . import docapi
from .widgets import FDialog, LengthSpin, color_button, combo, grid, heading
from . import modelapi


def _cell_at(win, x, y):
    """Put the cursor at view pixel (x, y); return (table, cell name) or None."""
    eng = win.engine
    tx, ty = eng.px_to_twips(x, y)
    eng.click_at(tx, ty)
    try:
        vc = modelapi.read_cursor(eng.model)
        t, c = vc.TextTable, vc.Cell
        if t is None or c is None:
            return None
        return t, c.CellName
    except Exception:
        return None


class TableDrawMode:
    """'draw': drag a rectangle to make a table, drag a line inside a table to
    split cells. 'erase': click a cell border to merge the cells beside it."""

    def __init__(self, win):
        self.win = win
        self.tool = None
        self.start = None
        self.cur = None
        view = win.engine.view
        view.connect("button-press-event", self._press)
        view.connect("motion-notify-event", self._motion)
        view.connect("button-release-event", self._release)
        view.connect_after("draw", self._draw)

    @property
    def active(self):
        return self.tool is not None

    def begin(self, tool):
        if self.tool == tool:
            self.stop()
            return
        self.tool = tool
        w = self.win.engine.view.get_window()
        if w is not None:
            try:
                w.set_cursor(Gdk.Cursor.new_from_name(w.get_display(),
                                                      "pencil" if tool == "draw" else "cell"))
            except Exception:
                pass
        self.win.status.flash("Drag to draw a table or a line inside one. Esc to stop."
                              if tool == "draw" else
                              "Click a line between cells to merge them. Esc to stop.")
        for k, b in getattr(self.win, "table_draw_buttons", {}).items():
            b.apply_state("true" if k == tool else "false")

    def stop(self):
        self.tool = None
        self.start = self.cur = None
        w = self.win.engine.view.get_window()
        if w is not None:
            w.set_cursor(None)
        for b in getattr(self.win, "table_draw_buttons", {}).values():
            b.apply_state("false")
        self.win.engine.view.queue_draw()

    def key(self, event):
        if self.active and event.keyval == Gdk.KEY_Escape:
            self.stop()
            return True
        return False

    def _press(self, view, ev):
        if not self.active or ev.button != 1:
            return False
        self.start = self.cur = (ev.x, ev.y)
        return True

    def _motion(self, view, ev):
        if not self.active or self.start is None:
            return False
        self.cur = (ev.x, ev.y)
        view.queue_draw()
        return True

    def _release(self, view, ev):
        if not self.active or self.start is None or ev.button != 1:
            return False
        (x0, y0), (x1, y1) = self.start, (ev.x, ev.y)
        self.start = self.cur = None
        view.queue_draw()
        tool = self.tool
        GLib.idle_add(lambda: (self._apply(tool, x0, y0, x1, y1), False)[1])
        return True

    def _draw(self, view, cr):
        if not self.active or self.start is None or self.cur is None:
            return False
        (x0, y0), (x1, y1) = self.start, self.cur
        cr.set_source_rgb(0.1, 0.1, 0.1)
        cr.set_line_width(1)
        cr.set_dash([3, 2])
        if self.tool == "draw":
            if abs(x1 - x0) > 12 and abs(y1 - y0) > 12:
                cr.rectangle(min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0))
            elif abs(x1 - x0) >= abs(y1 - y0):
                cr.move_to(x0, y0)
                cr.line_to(x1, y0)
            else:
                cr.move_to(x0, y0)
                cr.line_to(x0, y1)
            cr.stroke()
        return False

    # ------------------------------------------------------------ actions
    def _apply(self, tool, x0, y0, x1, y1):
        return

    def _new_table(self, m, x0, y0, x1, y1):
        from . import tablestyles
        eng = self.win.engine
        tx, ty = eng.px_to_twips(min(x0, x1), min(y0, y1))
        eng.click_at(tx, ty)

        def go():
            t = tablestyles.insert_table(m, 1, 1)
            z = eng.view.get_zoom() or 1.0
            to_mm = lambda px: int(px * 15 / z * 2540 / 1440)   # noqa: E731
            try:
                t.HoriOrient = 3                     # left, with an indent
                t.Width = max(500, to_mm(abs(x1 - x0)))
                t.getRows().getByIndex(0).Height = max(300, to_mm(abs(y1 - y0)))
                t.getRows().getByIndex(0).IsAutoHeight = True
            except Exception as e:
                print("draw table:", e)
            return False
        GLib.timeout_add(120, go)

    def _split(self, m, horizontal_line):
        vc = modelapi.read_cursor(m)
        try:
            t, c = vc.TextTable, vc.Cell
            cur = t.createCursorByCellName(c.CellName)
            um = m.getUndoManager()
            um.enterUndoContext("Draw Table")
            try:
                # a horizontal line splits the cell into rows
                cur.splitRange(1, horizontal_line)
            finally:
                um.leaveUndoContext()
        except Exception as e:
            print("split cell:", e)

    def _erase(self, m, x, y):
        """Merge the cells on both sides of the line nearest the click."""
        here = _cell_at(self.win, x, y)
        if here is None:
            return
        best = None
        for dx, dy, d in ((0, -7, "up"), (0, 7, "down"), (-7, 0, "left"), (7, 0, "right")):
            other = _cell_at(self.win, x + dx, y + dy)
            if other is not None and other[0] == here[0] and other[1] != here[1]:
                best = (d, other[1])
                break
        if best is None:
            self.win.status.flash("Click on a line between two cells.")
            return
        table, name = here
        try:
            names = sorted([name, best[1]], key=lambda n: _cell_key(n))
            cur = table.createCursorByCellName(names[0])
            cur.gotoCellByName(names[1], True)
            um = m.getUndoManager()
            um.enterUndoContext("Eraser")
            try:
                cur.mergeRange()
            finally:
                um.leaveUndoContext()
        except Exception as e:
            print("erase:", e)


def _cell_key(name):
    col = "".join(ch for ch in name.split(".")[0] if ch.isalpha())
    row = "".join(ch for ch in name.split(".")[0] if ch.isdigit())
    n = 0
    for ch in col:
        n = n * 26 + (ord(ch.upper()) - 64)
    return (int(row or 0), n)


# ------------------------------------------------------------ Insert Cells
def insert_cells_dialog(win):
    return


def shift_cells(t, name, down=True):
    """Make room at a cell: its column (or row) moves on by one cell, adding a
    row (or column) at the end."""
    rows, cols = t.getRows().getCount(), t.getColumns().getCount()
    col, row = _pos(t, name)
    if down:
        t.getRows().insertByIndex(rows, 1)
        for r in range(rows, row, -1):
            _copy(t.getCellByPosition(col, r - 1), t.getCellByPosition(col, r))
    else:
        t.getColumns().insertByIndex(cols, 1)
        for cc in range(cols, col, -1):
            _copy(t.getCellByPosition(cc - 1, row), t.getCellByPosition(cc, row))
    t.getCellByPosition(col, row).setString("")


def _pos(t, name):
    for r in range(t.getRows().getCount()):
        for c in range(t.getColumns().getCount()):
            try:
                if t.getCellByPosition(c, r).CellName == name:
                    return c, r
            except Exception:
                pass
    return 0, 0


def _copy(src, dst):
    dst.setString(src.getString())
    for p in ("BackColor", "VertOrient"):
        try:
            setattr(dst, p, getattr(src, p))
        except Exception:
            pass


# ------------------------------------------------------------ Table Properties
def properties_dialog(win, page=0):
    from .widgets import fmt_len
    return


def _set(spin, mm100):
    if hasattr(spin, "set_mm100"):
        spin.set_mm100(mm100)
    else:
        spin.set_value(mm100)


def column_widths(table, total):
    """Column widths (mm100) of the first row."""
    try:
        seps = list(table.TableColumnSeparators)
        rel = table.TableColumnRelativeSum
    except Exception:
        return [total]
    edges = [0] + [s.Position for s in seps] + [rel]
    return [int((b - a) * total / float(rel)) for a, b in zip(edges, edges[1:])]


def set_column_widths(table, edits, widths):
    seps = list(table.TableColumnSeparators)
    rel = table.TableColumnRelativeSum
    total = sum(widths)
    new = list(widths)
    for i, w in edits.items():
        if i < len(new):
            diff = w - new[i]
            new[i] = w
            if i + 1 < len(new):                 # the next column gives way
                new[i + 1] = max(100, new[i + 1] - diff)
    s = sum(new) or 1
    pos = 0
    for k, sep in enumerate(seps):
        pos += new[k]
        sep.Position = int(pos * rel / float(s))
    table.TableColumnSeparators = tuple(seps)
    if abs(s - total) > 50 and table.HoriOrient != 6:
        table.Width = s
