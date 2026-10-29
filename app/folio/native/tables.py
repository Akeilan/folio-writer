"""Table Layout and Table Design for the new engine: table styles written as
real Word table style definitions, style options, cell size, alignment,
borders and shading."""
from .. import tablestyles as TS

MM = 2540.0 / 1440.0
TOPT = {"header": ("w:firstRow", 0x20), "total": ("w:lastRow", 0x40),
        "first_col": ("w:firstColumn", 0x80), "last_col": ("w:lastColumn", 0x100),
        "banded_rows": ("w:noHBand", 0x200), "banded_cols": ("w:noVBand", 0x400)}


# ------------------------------------------------------------- style XML
def _ids(kind, accent):
    """Word's name and style id for a gallery entry."""
    names = dict((k, n) for n, k in TS.PLAIN + TS.GRID + TS.LIST)
    base = names.get(kind, "Table Grid")
    an = next((n for n, c in TS.ACCENTS if c == accent and n), "")
    name = base + (" " + an if an else "")
    sid = base.replace(" ", "") + ("-" + an.replace(" ", "") if an else "")
    return name, sid


def _border_xml(tag, b):
    if b is None:
        return '<w:%s w:val="nil"/>' % tag
    w, color = b
    sz = max(2, int(round(w * 8)))
    return '<w:%s w:val="single" w:sz="%d" w:space="0" w:color="%06X"/>' % (tag, sz, color & 0xFFFFFF)


def _rpr(s, base):
    out = ""
    if s["bold"] != base["bold"]:
        out += "<w:b/><w:bCs/>" if s["bold"] else '<w:b w:val="0"/><w:bCs w:val="0"/>'
    if s.get("caps") and not base.get("caps"):
        out += "<w:caps/>"
    if s["color"] != base["color"] and s["color"] >= 0:
        out += '<w:color w:val="%06X"/>' % s["color"]
    return "<w:rPr>%s</w:rPr>" % out if out else ""


def _tcpr(s, base, sides=("top", "left", "bottom", "right")):
    out = ""
    bd = ""
    for side in sides:
        if s[side] != base[side]:
            bd += _border_xml(side, s[side])
    if bd:
        out += "<w:tcBorders>%s</w:tcBorders>" % bd
    if s["fill"] != base["fill"]:
        if s["fill"] >= 0:
            out += '<w:shd w:val="clear" w:color="auto" w:fill="%06X"/>' % s["fill"]
        else:
            out += '<w:shd w:val="clear" w:color="auto" w:fill="auto"/>'
    return "<w:tcPr>%s</w:tcPr>" % out if out else ""


def style_xml(kind, accent):
    """(id, XML of a w:style) for a Plain/Grid/List table style, built from the
    same per-cell rules the gallery thumbnails use."""
    name, sid = _ids(kind, accent)
    R = C = 8
    none = {k: False for k in TS.DEFAULT_OPTS}
    cell = lambda opts, r, c: TS.cell(kind, accent, dict(none, **opts), r, c, R, C)  # noqa: E731
    base = cell({}, 3, 3)
    top = cell({}, 0, 3)["top"]
    bottom = cell({}, R - 1, 3)["bottom"]
    left = cell({}, 3, 0)["left"]
    right = cell({}, 3, C - 1)["right"]
    tbl_borders = "".join(_border_xml(t, b) for t, b in (
        ("top", top), ("left", left), ("bottom", bottom), ("right", right),
        ("insideH", base["top"]), ("insideV", base["left"])))
    whole_rpr = '<w:rPr><w:color w:val="%06X"/></w:rPr>' % base["color"] if base["color"] >= 0 else ""
    whole_tc = ('<w:tcPr><w:shd w:val="clear" w:color="auto" w:fill="%06X"/></w:tcPr>' % base["fill"]
                if base["fill"] >= 0 else "")
    conds = ""
    for typ, opts, r, c in (("firstRow", {"header": True}, 0, 3),
                            ("lastRow", {"total": True}, R - 1, 3),
                            ("firstCol", {"first_col": True}, 3, 0),
                            ("lastCol", {"last_col": True}, 3, C - 1),
                            ("band1Vert", {"banded_cols": True}, 3, 2),
                            ("band1Horz", {"banded_rows": True}, 2, 3)):
        s = cell(opts, r, c)
        # compare with the same cell without the option (outer edges stay)
        plain = cell({}, r, c)
        rpr = _rpr(s, plain)
        tcpr = _tcpr(s, plain)
        if rpr or tcpr:
            conds += '<w:tblStylePr w:type="%s">%s%s</w:tblStylePr>' % (typ, rpr, tcpr)
    xml = ('<w:style w:type="table" w:styleId="%s"><w:name w:val="%s"/>'
           '<w:basedOn w:val="TableNormal"/><w:uiPriority w:val="%d"/>'
           '<w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/></w:pPr>%s'
           '<w:tblPr><w:tblStyleRowBandSize w:val="1"/><w:tblStyleColBandSize w:val="1"/>'
           '<w:tblBorders>%s</w:tblBorders></w:tblPr>%s%s</w:style>'
           % (sid, name, 39 if kind == "grid" else 40, whole_rpr, tbl_borders, whole_tc, conds))
    return sid, xml


# ------------------------------------------------------------- actions
def _ed(win):
    return win.engine.ed


def _done(win):
    win.engine.view.after_edit()


def apply_style(win, kind, accent):
    ed = _ed(win)
    if not ed.cell_name():
        return
    sid, xml = style_xml(kind, accent)
    ed.begin_group("Table Style")
    ed.add_style_xml(xml)
    ed.table_apply("table", [("w:tblStyle", [("w:val", sid)])], "Table Style")
    ed.end_group()
    _done(win)


def set_option(win, key):
    ed = _ed(win)
    info = ed.table_info()
    if info is None or key not in TOPT:
        return
    on = not info[key]
    info[key] = on
    bits = 0
    attrs = []
    for k, (attr, bit) in TOPT.items():
        v = info[k]
        if k.startswith("banded"):
            if not v:
                bits |= bit
            attrs.append((attr, "0" if v else "1"))
        else:
            if v:
                bits |= bit
            attrs.append((attr, "1" if v else "0"))
    ed.table_apply("table", [("w:tblLook", [("w:val", "%04X" % bits)] + attrs)], "Table Style Options")
    _done(win)


def set_row_height(win, mm100):
    _ed(win).table_apply("rows", [("w:trHeight", [("w:val", str(int(round(mm100 / MM)))),
                                                  ("w:hRule", "atLeast")])], "Row Height")
    _done(win)


def set_col_width(win, mm100):
    ed = _ed(win)
    widths = list(ed.grid_widths())
    cols = ed.selected_grid_cols()
    if not widths or cols is None:
        return
    tw = int(round(mm100 / MM))
    for i in range(cols[0], min(cols[1], len(widths))):
        widths[i] = tw
    ed.set_grid_widths(widths, "Column Width")
    _done(win)


def distribute(win, what):
    ed = _ed(win)
    if what == "cols":
        widths = list(ed.grid_widths())
        if widths:
            each = sum(widths) // len(widths)
            ed.set_grid_widths([each] * len(widths), "Distribute Columns")
    _done(win)


def autofit(win, how):
    ed = _ed(win)
    if how == "contents":
        ed.autofit_contents()
    elif how == "window":
        ed.table_apply("table", [("w:tblW", [("w:w", "5000"), ("w:type", "pct")]),
                                 ("w:tblLayout", None)], "AutoFit Window")
    elif how == "fixed":
        ed.table_apply("table", [("w:tblLayout", [("w:type", "fixed")])], "Fixed Column Width")
    _done(win)


def align_cells(win, h, v):
    ed = _ed(win)
    jc = {"left": None, "center": [("w:val", "center")], "right": [("w:val", "right")]}[h]
    va = {"top": None, "center": [("w:val", "center")], "bottom": [("w:val", "bottom")]}[v]
    ed.begin_group("Cell Alignment")
    ed.table_apply("cell_paras", [("w:jc", jc)], "Cell Alignment")
    ed.table_apply("cells", [("w:vAlign", va)], "Cell Alignment")
    ed.end_group()
    _done(win)


def repeat_header(win):
    ed = _ed(win)
    on = True
    ed.table_apply("rows", [("w:tblHeader", [] if on else None)], "Repeat Header Rows")
    _done(win)


def shading(win, color):
    ed = _ed(win)
    if color is None or color < 0:
        ed.table_apply("cells", [("w:shd", None)], "Shading")
    else:
        ed.table_apply("cells", [("w:shd", [("w:val", "clear"), ("w:color", "auto"),
                                            ("w:fill", "%06X" % (color & 0xFFFFFF))])], "Shading")
    _done(win)


def borders(win, which, width_pt=0.5, color=-1):
    """Borders menu: all, outside, inside, none, top, bottom, left, right,
    inside_h, inside_v."""
    ed = _ed(win)
    line = [("w:val", "single"), ("w:sz", str(max(2, int(round(width_pt * 8))))),
            ("w:space", "0"), ("w:color", "%06X" % color if color >= 0 else "auto")]
    nil = [("w:val", "nil")]
    all6 = ("top", "left", "bottom", "right", "insideH", "insideV")
    if which in ("all", "outside", "inside", "none"):
        on = {"all": all6, "outside": all6[:4], "inside": all6[4:], "none": ()}[which]
        ed.begin_group("Borders")
        ed.set_borders("table", [(s, line if s in on else nil) for s in all6])
        # cell borders would hide the table's: they go
        ed.table_apply("cells", [("w:tcBorders", None)], "Borders")
        ed.end_group()
    elif which in ("diag-down", "diag-up"):
        # diagonal lines across the cells: a second click takes them off
        side = "tl2br" if which == "diag-down" else "tr2bl"
        ed.set_borders("cells", [(side, nil if ed.cell_border_on(side) else line)])
    else:
        side = {"inside_h": "insideH", "inside_v": "insideV"}.get(which, which)
        ed.set_borders("cells", [(side, line)])
    _done(win)


def borders_menu(win, which):
    """Borders drop-down: the selected cells in a table, else paragraphs."""
    ed = _ed(win)
    which = {"inside-h": "inside_h", "inside-v": "inside_v"}.get(which, which)
    if ed.cell_name():
        borders(win, which)
        return
    line = [("w:val", "single"), ("w:sz", "4"), ("w:space", "1"), ("w:color", "auto")]
    nil = [("w:val", "nil")]
    sides = ("top", "left", "bottom", "right", "between")
    if which in ("all", "outside", "none", "inside", "inside_h"):
        on = {"all": sides, "outside": sides[:4], "none": (), "inside": ("between",),
              "inside_h": ("between",)}[which]
        ed.set_borders("paras", [(s, line if s in on else None) for s in sides])
    elif which in sides:
        ed.set_borders("paras", [(which, line)])
    _done(win)


def text_direction(win):
    if _ed(win).cycle_text_direction():
        _done(win)


def distribute_rows(win):
    if _ed(win).distribute_rows():
        _done(win)


TW = 1440.0 / 2540.0   # twips per 1/100 mm


def split_cells_dialog(win):
    from gi.repository import Gtk
    from ..widgets import FDialog, grid
    ed = _ed(win)
    if not ed.cell_name():
        return
    d = FDialog(win, "Split Cells")
    cols = Gtk.SpinButton.new_with_range(1, 63, 1)
    cols.set_value(2)
    rows = Gtk.SpinButton.new_with_range(1, 63, 1)
    rows.set_value(1)
    d.add(grid([["Number of _columns:", cols], ["Number of _rows:", rows]]))
    merge = Gtk.CheckButton.new_with_mnemonic("_Merge cells before split")
    merge.set_active(True)
    d.add(merge)
    r = d.ask()
    c, n, m = int(cols.get_value()), int(rows.get_value()), merge.get_active()
    d.done()
    if r != Gtk.ResponseType.OK:
        return
    ed.begin_group("Split Cells")
    if m and ed.has_selection():
        ed.table_command("merge")
    ed.split_cells(c, n)
    ed.end_group()
    _done(win)


def split_table(win):
    if _ed(win).split_table():
        _done(win)


def select(win, what):
    if _ed(win).select_table_part(what):
        win.engine.view.after_move()


def properties_dialog(win, page=0):
    """Table Properties: Table, Row, Column, Cell and Alt Text."""
    from gi.repository import Gtk
    from ..widgets import FDialog, LengthSpin, combo, grid
    ed = _ed(win)
    tp = ed.table_props()
    if tp is None:
        return
    widths = list(ed.grid_widths())
    cols = ed.selected_grid_cols() or (0, 1)
    d = FDialog(win, "Table Properties")
    nb = Gtk.Notebook()
    d.add(nb)

    def opt_len(on, mm100):
        cb = Gtk.CheckButton.new_with_mnemonic("_Preferred width:")
        sp = LengthSpin(mm100, 0, 55880)
        cb.set_active(on)
        sp.set_sensitive(on)
        cb.connect("toggled", lambda b: sp.set_sensitive(b.get_active()))
        return cb, sp

    def tab(title, rows, extra=()):
        b = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        b.set_border_width(12)
        b.pack_start(grid(rows), False, False, 0)
        for w in extra:
            b.pack_start(w, False, False, 0)
        nb.append_page(b, Gtk.Label(label=title))
    # table
    w, wt = tp["width"]
    t_on, t_w = opt_len(wt == "dxa" and w > 0, w / TW if wt == "dxa" else 0)
    t_pct = Gtk.CheckButton.new_with_mnemonic("Percent of page width")
    t_pct.set_active(wt == "pct")
    aligns = ["left", "center", "right"]
    t_al = combo(["Left", "Center", "Right"], aligns.index(tp["jc"]) if tp["jc"] in aligns else 0)
    t_ind = LengthSpin(tp["ind"] / TW, -55880, 55880)
    tab("Table", [[t_on, t_w], ["", t_pct], ["Alignment:", t_al], ["_Indent from left:", t_ind]])
    # row
    r_on = Gtk.CheckButton.new_with_mnemonic("_Specify height:")
    r_on.set_active(tp["row_height"] > 0)
    r_h = LengthSpin(tp["row_height"] / TW, 0, 55880)
    r_rule = combo(["At least", "Exactly"], 1 if tp["row_rule"] == "exact" else 0)
    r_split = Gtk.CheckButton.new_with_mnemonic("Allow row to _break across pages")
    r_split.set_active(not tp["cant_split"])
    r_head = Gtk.CheckButton.new_with_mnemonic("Repeat as _header row at the top of each page")
    r_head.set_active(tp["header"])
    tab("Row", [[r_on, r_h], ["Row height is:", r_rule]], [r_split, r_head])
    # column
    cw = sum(widths[cols[0]:cols[1]]) if widths else 0
    c_on, c_w = opt_len(cw > 0, cw / TW)
    tab("Column", [[c_on, c_w]])
    # cell
    w, wt = tp["cell_width"]
    e_on, e_w = opt_len(w > 0 and wt == "dxa", w / TW if wt == "dxa" else 0)
    valigns = ["top", "center", "bottom"]
    e_va = combo(["Top", "Center", "Bottom"], valigns.index(tp["valign"]) if tp["valign"] in valigns else 0)
    tab("Cell", [[e_on, e_w], ["Vertical alignment:", e_va]])
    # alt text
    a_title = Gtk.Entry()
    a_title.set_text(tp["caption"])
    a_desc = Gtk.Entry()
    a_desc.set_text(tp["description"])
    tab("Alt Text", [["_Title:", a_title], ["_Description:", a_desc]])
    nb.set_current_page(page)
    r = d.ask()
    vals = dict(t_on=t_on.get_active(), t_w=t_w.mm100, t_pct=t_pct.get_active(), t_al=t_al.get_active(),
                t_ind=t_ind.mm100, r_on=r_on.get_active(), r_h=r_h.mm100, r_rule=r_rule.get_active(),
                r_split=r_split.get_active(), r_head=r_head.get_active(), c_on=c_on.get_active(),
                c_w=c_w.mm100, e_on=e_on.get_active(), e_w=e_w.mm100, e_va=e_va.get_active(),
                a_title=a_title.get_text(), a_desc=a_desc.get_text())
    d.done()
    if r != Gtk.ResponseType.OK:
        return
    v = vals
    tw = lambda mm: str(int(round(mm * TW)))  # noqa: E731
    ed.begin_group("Table Properties")
    if v["t_pct"]:
        width = [("w:w", "5000"), ("w:type", "pct")]
    elif v["t_on"]:
        width = [("w:w", tw(v["t_w"])), ("w:type", "dxa")]
    else:
        width = [("w:w", "0"), ("w:type", "auto")]
    ed.table_apply("table", [
        ("w:tblW", width),
        ("w:jc", None if v["t_al"] == 0 else [("w:val", aligns[v["t_al"]])]),
        ("w:tblInd", [("w:w", tw(v["t_ind"])), ("w:type", "dxa")] if v["t_al"] == 0 else None),
        ("w:tblCaption", [("w:val", v["a_title"])] if v["a_title"] else None),
        ("w:tblDescription", [("w:val", v["a_desc"])] if v["a_desc"] else None)], "Table Properties")
    ed.table_apply("rows", [
        ("w:trHeight", [("w:val", tw(v["r_h"])), ("w:hRule", "exact" if v["r_rule"] else "atLeast")]
         if v["r_on"] else None),
        ("w:cantSplit", None if v["r_split"] else []),
        ("w:tblHeader", [] if v["r_head"] else None)], "Table Properties")
    if v["c_on"] and widths:
        new = list(widths)
        span = max(1, cols[1] - cols[0])
        for i in range(cols[0], min(cols[1], len(new))):
            new[i] = int(round(v["c_w"] * TW / span))
        if new != widths:
            ed.set_grid_widths(new, "Table Properties")
    ed.table_apply("cells", [
        ("w:vAlign", None if v["e_va"] == 0 else [("w:val", valigns[v["e_va"]])])], "Table Properties")
    if v["e_on"] and not v["c_on"]:
        ed.table_apply("cells", [("w:tcW", [("w:w", tw(v["e_w"])), ("w:type", "dxa")])], "Table Properties")
    ed.end_group()
    _done(win)


def insert_cells_dialog(win):
    from gi.repository import Gtk
    from ..widgets import FDialog
    ed = _ed(win)
    if not ed.cell_name():
        return
    d = FDialog(win, "Insert Cells")
    row = Gtk.RadioButton.new_with_mnemonic(None, "Insert entire _row")
    col = Gtk.RadioButton.new_with_mnemonic_from_widget(row, "Insert entire _column")
    d.add(row)
    d.add(col)
    r = d.ask()
    which = "insert_rows_above" if row.get_active() else "insert_cols_left"
    d.done()
    if r == Gtk.ResponseType.OK and ed.table_command(which):
        _done(win)


DISPATCH = {
    "set_row_height": set_row_height, "set_col_width": set_col_width, "autofit": autofit,
    "align_cells": align_cells, "repeat_header": repeat_header, "distribute": distribute,
    "text_direction": text_direction, "distribute_rows": distribute_rows,
}


def call(win, fn, *args):
    f = DISPATCH.get(fn)
    if f is None:
        return False
    f(win, *args)
    return True


# ================================================================ Draw Table / Eraser
class TableDrawTool:
    """Table Layout > Draw Table and Eraser. 'draw': drag a rectangle outside
    a table to make one that size, or a line across a cell to split it;
    'erase': click the line between two cells to merge them. Esc stops."""

    def __init__(self, win):
        self.win = win
        self.tool = None
        self.start = None
        self.cur = None

    @property
    def active(self):
        return self.tool is not None

    def begin(self, tool):
        from gi.repository import Gdk
        if self.tool == tool:
            self.stop()
            return
        self.tool = tool
        w = self.win.engine.view.get_window()
        if w is not None:
            try:
                w.set_cursor(Gdk.Cursor.new_from_name(w.get_display(), "pencil" if tool == "draw" else "cell"))
            except Exception:
                pass
        self.win.status.flash("Drag to draw a table or a line inside one. Esc to stop."
                              if tool == "draw" else "Click a line between cells to merge them. Esc to stop.")
        for k, b in getattr(self.win, "table_draw_buttons", {}).items():
            b.apply_state("true" if k == tool else "false")

    def stop(self):
        self.tool = None
        self.start = self.cur = None
        v = self.win.engine.view
        w = v.get_window()
        if w is not None:
            w.set_cursor(None)
        for b in getattr(self.win, "table_draw_buttons", {}).values():
            b.apply_state("false")
        v.queue_draw()

    def key(self, event):
        from gi.repository import Gdk
        if self.active and event.keyval == Gdk.KEY_Escape:
            self.stop()
            return True
        return False

    def press(self, ev):
        if ev.button != 1:
            return False
        self.start = self.cur = (ev.x, ev.y)
        return True

    def motion(self, ev):
        if self.start is None:
            return True
        self.cur = (ev.x, ev.y)
        self.win.engine.view.queue_draw()
        return True

    def release(self, ev):
        if self.start is None or ev.button != 1:
            return False
        (x0, y0), (x1, y1) = self.start, (ev.x, ev.y)
        self.start = self.cur = None
        try:
            if self.tool == "draw":
                self._draw_at(x0, y0, x1, y1)
            else:
                self._erase_at(x1, y1)
        except Exception as e:
            print("draw table:", e)
        self.win.engine.view.queue_draw()
        return True

    def draw(self, cr):
        if self.start is None or self.cur is None or self.tool != "draw":
            return
        (x0, y0), (x1, y1) = self.start, self.cur
        cr.save()
        cr.set_source_rgb(0.1, 0.1, 0.1)
        cr.set_line_width(1)
        cr.set_dash([3, 2])
        if abs(x1 - x0) > 12 and abs(y1 - y0) > 12:
            cr.rectangle(min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0))
        elif abs(x1 - x0) >= abs(y1 - y0):
            cr.move_to(x0, y0)
            cr.line_to(x1, y0)
        else:
            cr.move_to(x0, y0)
            cr.line_to(x0, y1)
        cr.stroke()
        cr.restore()

    # ------------------------------------------------------------ actions
    def _click(self, x, y, extend=False):
        v = self.win.engine.view
        hit = v.page_at(x, y)
        if hit is None:
            return None
        _ed(self.win).click(hit[0], hit[1], hit[2], extend)
        return hit

    def _draw_at(self, x0, y0, x1, y1):
        ed = _ed(self.win)
        v = self.win.engine.view
        s = v.ppp
        box = abs(x1 - x0) > 12 and abs(y1 - y0) > 12
        if not self._click(min(x0, x1) + 2, min(y0, y1) + 2):
            return
        in_table = bool(ed.cell_name())
        if box and not in_table:
            # a new table as big as the rectangle (points -> 1/100 mm)
            ed.begin_group("Draw Table")
            try:
                ed.insert_table(1, 1)
                set_col_width(self.win, abs(x1 - x0) / s * 2540.0 / 72.0)
                set_row_height(self.win, abs(y1 - y0) / s * 2540.0 / 72.0)
            finally:
                ed.end_group()
            _done(self.win)
            return
        if not in_table:
            return
        # a line inside a cell splits it
        self._click((x0 + x1) / 2.0, (y0 + y1) / 2.0)
        if not ed.cell_name():
            return
        if abs(x1 - x0) >= abs(y1 - y0):
            ed.split_cells(1, 2)
        else:
            ed.split_cells(2, 1)
        _done(self.win)

    def _erase_at(self, x, y):
        """Merge the two cells either side of the line at (x, y)."""
        ed = _ed(self.win)
        for dx, dy in ((5, 0), (0, 5)):
            if not self._click(x - dx, y - dy):
                continue
            a = ed.cell_name()
            if not a:
                continue
            self._click(x + dx, y + dy)
            b = ed.cell_name()
            if b and b != a:
                self._click(x - dx, y - dy)
                self._click(x + dx, y + dy, True)
                if ed.table_command("merge"):
                    _done(self.win)
                    return
        self.win.status.flash("Click a line between two cells to merge them.")


# ================================================================ Data group / Table Options
def _table_index(ed):
    """The body table the caret is in: its index for table_cells(), or None."""
    node = ed.caret_pos()[0]
    for kind, _n, i in ed.body_blocks():
        if kind == "t":
            for row in ed.table_cells(i):
                for cell in row:
                    if node in cell:
                        return i
    return None


def convert_dialog(win):
    """Table Layout > Convert to Text: the cells as text, one row a paragraph,
    separated by tabs (or another character)."""
    from gi.repository import Gtk
    from ..widgets import FDialog
    ed = _ed(win)
    n = _table_index(ed) if ed.cell_name() else None
    if n is None:
        win.status.flash("Put the cursor in a table first.")
        return
    d = FDialog(win, "Convert Table To Text")
    d.add(Gtk.Label(label="Separate text with", xalign=0))
    marks = Gtk.RadioButton.new_with_mnemonic(None, "_Paragraph marks")
    tabs = Gtk.RadioButton.new_with_mnemonic_from_widget(marks, "_Tabs")
    commas = Gtk.RadioButton.new_with_mnemonic_from_widget(marks, "Co_mmas")
    other = Gtk.RadioButton.new_with_mnemonic_from_widget(marks, "_Other:")
    oe = Gtk.Entry(text="-")
    oe.set_width_chars(3)
    tabs.set_active(True)
    for w in (marks, tabs, commas):
        d.add(w)
    row = Gtk.Box(spacing=6)
    row.pack_start(other, False, False, 0)
    row.pack_start(oe, False, False, 0)
    d.add(row)
    r = d.ask()
    sep = "\n" if marks.get_active() else "\t" if tabs.get_active() else "," if commas.get_active() \
        else (oe.get_text() or "-")
    d.done()
    if r != Gtk.ResponseType.OK:
        return
    lines = []
    for row in ed.table_cells(n):
        cells = [" ".join(ed.para_text_of(p).replace("￼", "") for p in cell) for cell in row]
        lines.append(sep.join(cells))
    ed.begin_group("Convert Table to Text")
    try:
        ed.table_command("delete_table")
        ed.type_text("\n".join(lines))
    finally:
        ed.end_group()
    _done(win)


FUNCS = ("ABS", "AND", "AVERAGE", "COUNT", "DEFINED", "FALSE", "IF", "INT", "MAX", "MIN", "MOD",
         "NOT", "OR", "PRODUCT", "ROUND", "SIGN", "SUM", "TRUE")
NUMBER_FORMATS = ("#,##0", "#,##0.00", "$#,##0.00;($#,##0.00)", "0", "0%", "0.00", "0.00%")


def _default_formula(ed):
    """=SUM(ABOVE) under numbers, =SUM(LEFT) beside them, as Word suggests."""
    n = _table_index(ed)
    if n is None:
        return "=SUM(ABOVE)"
    node = ed.caret_pos()[0]
    rows = ed.table_cells(n)
    for r, row in enumerate(rows):
        for c, cell in enumerate(row):
            if node in cell:
                def num(rr, cc):
                    try:
                        t = " ".join(ed.para_text_of(p) for p in rows[rr][cc]).replace(",", "").strip()
                        float(t)
                        return True
                    except (ValueError, IndexError):
                        return False
                if r > 0 and num(r - 1, c):
                    return "=SUM(ABOVE)"
                if c > 0 and num(r, c - 1):
                    return "=SUM(LEFT)"
    return "=SUM(ABOVE)"


def formula_dialog(win):
    """Table Layout > Formula: a formula field (= SUM(ABOVE) and the like)."""
    from gi.repository import Gtk
    from ..widgets import FDialog, grid
    ed = _ed(win)
    if not ed.cell_name():
        win.status.flash("Put the cursor in a table cell first.")
        return
    d = FDialog(win, "Formula")
    fe = Gtk.Entry(text=_default_formula(ed))
    fe.set_width_chars(36)
    fmt = Gtk.ComboBoxText.new_with_entry()
    for f in NUMBER_FORMATS:
        fmt.append_text(f)
    paste = Gtk.ComboBoxText()
    paste.append_text("Paste function")
    for f in FUNCS:
        paste.append_text(f)
    paste.set_active(0)

    def put(c):
        if c.get_active() > 0:
            pos = fe.get_position()
            fe.insert_text(FUNCS[c.get_active() - 1] + "()", pos)
            fe.set_position(pos + len(FUNCS[c.get_active() - 1]) + 1)
            c.set_active(0)
    paste.connect("changed", put)
    marks = Gtk.ComboBoxText()
    marks.append_text("Paste bookmark")
    names = list(ed.bookmark_names())
    for b in names:
        marks.append_text(b)
    marks.set_active(0)

    def put_mark(c):
        if c.get_active() > 0:
            fe.insert_text(names[c.get_active() - 1], fe.get_position())
            c.set_active(0)
    marks.connect("changed", put_mark)
    d.add(grid([["_Formula:", fe], ["_Number format:", fmt]]))
    row = Gtk.Box(spacing=8)
    row.pack_start(paste, True, True, 0)
    row.pack_start(marks, True, True, 0)
    d.add(row)
    r = d.ask()
    text, pic = fe.get_text().strip(), fmt.get_child().get_text().strip()
    d.done()
    if r != Gtk.ResponseType.OK or not text:
        return
    if not text.startswith("="):
        text = "=" + text
    instr = text + ((' \\# "%s"' % pic) if pic else "")
    ed.insert_field_now(instr)
    _done(win)


def cell_margins_dialog(win):
    """Table Layout > Cell Margins (Table Options): default cell margins."""
    from gi.repository import Gtk
    from ..widgets import FDialog, LengthSpin, grid, heading
    ed = _ed(win)
    cur = ed.table_cell_margins() if ed.cell_name() else None
    if cur is None:
        win.status.flash("Put the cursor in a table first.")
        return
    d = FDialog(win, "Table Options")
    spins = [LengthSpin(int(round(v * MM)), 0, 25400) for v in cur]
    d.add(heading("Default cell margins"))
    d.add(grid([["_Top:", spins[0], "_Left:", spins[2]],
                ["_Bottom:", spins[1], "_Right:", spins[3]]]))
    if d.ask() == Gtk.ResponseType.OK:
        tw = [int(round(s.mm100 / MM)) for s in spins]
        ed.set_table_cell_margins(*tw)
        _done(win)
    d.done()
