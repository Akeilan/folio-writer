"""Lists, as in the original: the numbered-list commands of the right-click
menu (Restart at 1, Continue Numbering, Set Numbering Value, Adjust List
Indents) and the Multilevel List gallery."""
from gi.repository import Gtk


ARABIC, UPPER, LOWER, ROMAN_UP, ROMAN_LOW, BULLET, NONE = 4, 0, 1, 2, 3, 6, 5
LISTTAB, SPACE, NOTHING = 0, 1, 2
INDENT = 635          # 0.25" per level (1/100 mm)


def _nwin(m):
    return m.eng.win


def in_numbered_list(m):
    i = m.eng.ed.list_info()
    return i is not None and not i[2]


def in_list(m):
    return m.eng.ed.list_info() is not None


# ---------------------------------------------------------------- numbering value
def restart_at(m, value=1):
    from .native import lists as NL
    return NL.restart_at(_nwin(m), value)


def continue_numbering(m):
    """Join this list onto the previous list (of the same kind)."""
    from .native import lists as NL
    return NL.continue_numbering(_nwin(m))


def set_numbering_value(win):
    from .native import lists as NL
    return NL.set_numbering_value(win)


def adjust_indents(win):
    from .native import lists as NL
    return NL.adjust_indents(win)


# ---------------------------------------------------------------- multilevel
def _lvl(kind, fmt, n, char=None, font=None):
    return {"kind": kind, "fmt": fmt, "char": char, "font": font, "n": n}


def _numbered(fmts):
    out = []
    for i in range(9):
        kind, fmt = fmts[i % len(fmts)]
        out.append(_lvl(kind, fmt.replace("#", "%%%d%%" % (i + 1)), i))
    return out


MULTI = [
    ("1.  a.  i.", _numbered([(ARABIC, "#."), (LOWER, "#."), (ROMAN_LOW, "#.")])),
    ("1)  a)  i)", _numbered([(ARABIC, "#)"), (LOWER, "#)"), (ROMAN_LOW, "#)")])),
    ("1.  1.1.  1.1.1.",
     [_lvl(ARABIC, "".join("%%%d%%." % (k + 1) for k in range(i + 1)), i) for i in range(9)]),
    ("•  ◦  ▪", [_lvl(BULLET, "", i, char="•◦▪"[i % 3], font="OpenSymbol") for i in range(9)]),
    ("Article I.  Section 1.01  (a)",
     [_lvl(ROMAN_UP, "Article %1%.", 0), _lvl(ARABIC, "Section %1%.%2%", 1),
      _lvl(LOWER, "(%3%)", 2), _lvl(ROMAN_LOW, "(%4%)", 3)] +
     [_lvl(ARABIC, "%%%d%%)" % (i + 1), i) for i in range(4, 9)]),
    ("I.  A.  1.  a)", _numbered([(ROMAN_UP, "#."), (UPPER, "#."), (ARABIC, "#."),
                                  (LOWER, "#)"), (LOWER, "(#)"), (ROMAN_LOW, "(#)")])),
]


def apply_multilevel(m, levels):
    from .native import lists as NL
    return NL.apply_multilevel(_nwin(m), levels)


def heading_numbering(m, chapter=False):
    """Number the Heading styles: '1 Heading 1', '1.1 Heading 2' (or
    'Chapter 1')."""
    from .native import lists as NL
    return NL.heading_numbering(_nwin(m), chapter)


def _preview(levels, W=96, H=78):
    da = Gtk.DrawingArea()
    da.set_size_request(W, H)

    def label(spec, counters):
        if spec["kind"] == BULLET:
            return spec["char"]
        s = spec["fmt"]
        for k in range(9):
            tok = "%%%d%%" % (k + 1)
            if tok in s:
                kind = levels[k]["kind"] if k < len(levels) else ARABIC
                s = s.replace(tok, _fmt_num(kind, counters[k]))
        return s

    def draw(_w, cr):
        cr.set_source_rgb(1, 1, 1)
        cr.paint()
        cr.set_source_rgb(0.2, 0.2, 0.2)
        cr.select_font_face("Sans")
        cr.set_font_size(7)
        counters = [1] * 9
        y = 12
        for i in range(3):
            x = 4 + i * 10
            t = label(levels[i], counters)
            cr.move_to(x, y)
            cr.show_text(t)
            ext = cr.text_extents(t)
            cr.set_source_rgb(0.65, 0.65, 0.65)
            cr.rectangle(x + ext.x_advance + 3, y - 4, W - x - ext.x_advance - 8, 2.5)
            cr.fill()
            cr.set_source_rgb(0.2, 0.2, 0.2)
            y += 22
        return False
    da.connect("draw", draw)
    return da


def _fmt_num(kind, n):
    if kind == UPPER:
        return chr(64 + n)
    if kind == LOWER:
        return chr(96 + n)
    if kind == ROMAN_UP:
        return ["I", "II", "III", "IV"][n - 1]
    if kind == ROMAN_LOW:
        return ["i", "ii", "iii", "iv"][n - 1]
    return str(n)


def multilevel_gallery(win):
    """The Multilevel List drop-down."""
    m = win.dialogs.model
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
    box.set_border_width(6)
    pop = Gtk.Popover()

    def head(t):
        lab = Gtk.Label(xalign=0)
        lab.set_markup("<b>%s</b>" % t)
        box.pack_start(lab, False, False, 0)

    head("List Library")
    flow = Gtk.FlowBox()
    flow.set_max_children_per_line(3)
    flow.set_min_children_per_line(3)
    flow.set_selection_mode(Gtk.SelectionMode.NONE)

    def add_tile(name, fn, levels):
        b = Gtk.Button()
        b.set_tooltip_text(name)
        b.add(_preview(levels))
        b.get_style_context().add_class("folio-gallery-tile")
        b.connect("clicked", lambda *_: (pop.popdown(), fn(), win.focus_document()))
        flow.add(b)

    add_tile("None", lambda: win.actions.cmd(".uno:RemoveBullets"),
             [_lvl(NONE, "", i) for i in range(9)])
    for name, levels in MULTI:
        add_tile(name, (lambda lv=levels: apply_multilevel(win.dialogs.model, lv)), levels)
    add_tile("1 Heading 1, 1.1 Heading 2", lambda: heading_numbering(win.dialogs.model),
             [_lvl(ARABIC, ".".join("%%%d%%" % (k + 1) for k in range(i + 1)), i)
              for i in range(9)])
    add_tile("Chapter 1 Heading 1", lambda: heading_numbering(win.dialogs.model, True),
             [_lvl(ARABIC, "Ch. %1%", 0)] +
             [_lvl(ARABIC, ".".join("%%%d%%" % (k + 1) for k in range(i + 1)), i)
              for i in range(1, 9)])
    box.pack_start(flow, False, False, 0)
    box.pack_start(Gtk.Separator(), False, False, 2)

    def menu_item(label, cb, sensitive=True):
        b = Gtk.Button(label=label)
        b.set_relief(Gtk.ReliefStyle.NONE)
        b.get_child().set_xalign(0)
        b.set_sensitive(sensitive)
        b.connect("clicked", lambda *_: (pop.popdown(), cb()))
        box.pack_start(b, False, False, 0)
        return b

    listed = m is not None and in_list(m)
    lvlbtn = Gtk.MenuButton(label="Change List Level")
    lvlbtn.set_relief(Gtk.ReliefStyle.NONE)
    lvlbtn.set_sensitive(listed)
    lm = Gtk.Menu()
    for i in range(9):
        mi = Gtk.MenuItem(label="Level %d" % (i + 1))
        mi.connect("activate", lambda _m, i=i: (pop.popdown(), set_level(win, i)))
        lm.append(mi)
    lm.show_all()
    lvlbtn.set_popup(lm)
    box.pack_start(lvlbtn, False, False, 0)
    menu_item("Define New Multilevel List...", lambda: define_dialog(win))
    box.show_all()
    pop.add(box)
    return pop


def set_level(win, lvl):
    """Change List Level: the selected list paragraphs to level lvl (0-8)."""
    ed = win.engine.ed
    info = ed.list_info() if ed is not None else None
    if info is None:
        return
    if lvl != info[1] and ed.change_list_level(lvl - info[1]):
        win.engine.view.after_edit()


KINDS = [("1, 2, 3, ...", ARABIC), ("I, II, III, ...", ROMAN_UP), ("i, ii, iii, ...", ROMAN_LOW),
         ("A, B, C, ...", UPPER), ("a, b, c, ...", LOWER), ("Bullet", BULLET), ("(none)", NONE)]


def define_dialog(win):
    """Define New Multilevel List: each level's number style, format and
    position."""
    from .widgets import FDialog
    from .widgets import LengthSpin, grid, combo
    levels = [dict(x) for x in MULTI[0][1]]
    for i, x in enumerate(levels):
        x["pos"] = INDENT * i
        x["indent"] = INDENT * (i + 1)
    d = FDialog(win, "Define New Multilevel List")
    hb = Gtk.Box(spacing=10)
    hb.set_border_width(10)
    lvlist = Gtk.ListBox()
    for i in range(9):
        lvlist.add(Gtk.Label(label=str(i + 1), xalign=0.5))
    hb.pack_start(lvlist, False, False, 0)
    right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    fmt = Gtk.Entry()
    kind = combo([k for k, _v in KINDS], 0)
    start = Gtk.SpinButton.new_with_range(0, 999, 1)
    start.set_value(1)
    pos = LengthSpin(0, 0, 55880)
    ind = LengthSpin(INDENT, 0, 55880)
    fol = combo(["Tab character", "Space", "Nothing"], 0)
    right.pack_start(grid([["Enter _formatting for number:", fmt],
                           ["_Number style for this level:", kind],
                           ["_Start at:", start],
                           ["_Aligned at:", pos], ["_Text indent at:", ind],
                           ["Follow number _with:", fol]]), False, False, 0)
    hint = Gtk.Label(label="Use %1%, %2%… for the numbers of levels 1, 2…", xalign=0)
    hint.get_style_context().add_class("dim-label")
    right.pack_start(hint, False, False, 0)
    hb.pack_start(right, True, True, 0)
    d.add(hb)
    cur = [0]
    loading = [False]

    def load(i):
        loading[0] = True
        x = levels[i]
        fmt.set_text(x["fmt"] if x["kind"] != BULLET else (x.get("char") or "•"))
        kind.set_active(next((j for j, (_k, v) in enumerate(KINDS) if v == x["kind"]), 0))
        start.set_value(x.get("start", 1))
        pos.set_value(x["pos"])
        ind.set_value(x["indent"])
        fol.set_active(x.get("follow", 0))
        loading[0] = False

    def store(*_):
        if loading[0]:
            return
        x = levels[cur[0]]
        x["kind"] = KINDS[kind.get_active()][1]
        if x["kind"] == BULLET:
            x["char"] = (fmt.get_text() or "•")[:1]
            x["font"] = "OpenSymbol"
        else:
            x["fmt"] = fmt.get_text()
        x["start"] = int(start.get_value())
        x["pos"], x["indent"] = pos.mm100, ind.mm100
        x["follow"] = fol.get_active()

    for w, sig in ((fmt, "changed"), (kind, "changed"), (start, "value-changed"),
                   (pos, "value-changed"), (ind, "value-changed"), (fol, "changed")):
        w.connect(sig, store)

    def pick(_lb, row):
        if row is None:
            return
        cur[0] = row.get_index()
        load(cur[0])
    lvlist.connect("row-selected", pick)
    lvlist.select_row(lvlist.get_row_at_index(0))
    load(0)
    d.show_all()
    ok = d.ask() == Gtk.ResponseType.OK
    if ok:
        store()
        from .native import lists as nl
        nl.apply_multilevel(win, [dict(x, n=i) for i, x in enumerate(levels)])
    d.destroy()
    win.focus_document()
