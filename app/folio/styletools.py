"""Styles pane extras: the Style Inspector and the Manage Styles dialog, with Folio's
engine (W3-04: the document's styles and the formatting at the cursor, read from it)."""
import html

from gi.repository import GLib, Gtk, Pango

from .panes import Pane
from .widgets import FDialog

ALIGN = {"left": "Left", "start": "Left", "right": "Right", "end": "Right", "center": "Centered",
         "both": "Justified", "distribute": "Distributed"}
# paragraph properties Clear Formatting (paragraph) takes back to the style's
PARA_CLEAR = ["w:jc", "w:ind", "w:spacing", "w:shd", "w:keepLines", "w:keepNext", "w:widowControl",
              "w:pageBreakBefore", "w:pBdr", "w:tabs", "w:contextualSpacing"]
RUN_CLEAR = ["w:rFonts", "w:b", "w:bCs", "w:i", "w:iCs", "w:caps", "w:smallCaps", "w:strike", "w:dstrike",
             "w:color", "w:spacing", "w:sz", "w:szCs", "w:highlight", "w:u", "w:vertAlign", "w:shd"]


def _pt(tw):
    return "%g pt" % round((tw or 0) / 20.0, 1)


def _len(tw):
    from .widgets import fmt_len
    try:
        return fmt_len(int(round((tw or 0) * 2540 / 1440.0)))
    except Exception:
        return "%.2f\"" % ((tw or 0) / 1440.0)


def _line(rule, v):
    if rule == "auto":
        return {240: "Single", 360: "1.5 lines", 480: "Double"}.get(v, "Multiple %g li" % round(v / 240.0, 2))
    return ("Exactly %s" if rule == "exact" else "At least %s") % _pt(v)


def _style_ids(ed):
    return {s[0]: s for s in ed.style_list()}


def direct_formatting(ed):
    """([paragraph descriptions], [text descriptions]): formatting at the cursor on top of
    its styles."""
    st = ed.state() or {}
    pid = st.get("style_id") or ""
    cid = st.get("char_style_id") or ""
    try:
        pv = ed.style_para_values(pid) if pid else {}
        rv = ed.style_run_values(cid) if cid else (ed.style_run_values(pid) if pid else {})
    except Exception:
        return [], []
    para, text = [], []
    if ALIGN.get(st.get("align")) != ALIGN.get(pv.get("align", "left")):
        para.append("Alignment: %s" % ALIGN.get(st.get("align"), st.get("align")))
    for key, skey, label in (("ind_left", "ind_left", "Indent: Left"), ("ind_right", "ind_right", "Indent: Right")):
        if (st.get(key) or 0) != (pv.get(skey) or 0):
            para.append("%s: %s" % (label, _len(st.get(key))))
    if (st.get("ind_first") or 0) != (pv.get("ind_first") or 0):
        v = st.get("ind_first") or 0
        para.append("First line: %s" % _len(v) if v >= 0 else "Hanging: %s" % _len(-v))
    for key, skey, label in (("space_before", "before", "Space Before"), ("space_after", "after", "Space After")):
        if (st.get(key) or 0) != (pv.get(skey) or 0):
            para.append("%s: %s" % (label, _pt(st.get(key))))
    if (st.get("line"), st.get("line_rule")) != (pv.get("line", 240), pv.get("line_rule", "auto")):
        para.append("Line spacing: %s" % _line(st.get("line_rule"), st.get("line") or 240))
    if (st.get("font") or "") != (rv.get("font") or ""):
        text.append(st.get("font") or "")
    if abs(float(st.get("size") or 0) - float(rv.get("size") or 0)) > 0.01:
        text.append("%g pt" % float(st.get("size") or 0))
    for key, on, off in (("bold", "Bold", "Not Bold"), ("italic", "Italic", "Not Italic"),
                         ("strike", "Strikethrough", "No strikethrough")):
        a = st.get(key) is True
        if a != bool(rv.get(key)):
            text.append(on if a else off)
    u = st.get("underline") or "none"
    if (u != "none") != ((rv.get("underline") or "none") != "none"):
        text.append("Underline" if u != "none" else "No underline")
    col = st.get("color") or "auto"
    scol = rv.get("color", -1)
    scol = "auto" if scol is None or scol < 0 else "%06X" % scol
    if col.upper() != scol.upper() and not (col == "auto" and scol == "000000"):
        text.append("Font color: %s" % ("Automatic" if col == "auto" else "#" + col))
    if (st.get("highlight") or "none") != "none":
        text.append("Highlight: %s" % st.get("highlight"))
    va = st.get("vert_align") or "baseline"
    if va != (rv.get("vert_align") or "baseline"):
        text.append({"superscript": "Superscript", "subscript": "Subscript"}.get(va, "Normal"))
    return para, text


def clear_para(ed):
    ed.apply_para([(n, None) for n in PARA_CLEAR], "Clear Paragraph Formatting")


def clear_char(ed):
    ed.apply_run([(n, None) for n in RUN_CLEAR], "Clear Character Formatting")


class StyleInspector(Pane):
    TITLE = "Style Inspector"
    WIDTH = 260

    def __init__(self, win):
        Pane.__init__(self, win)
        self._timer = None
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, margin=6)
        self.para_style, self.para_plus = self._section(box, "Paragraph formatting",
                                                         self.reset_para_style,
                                                         self.clear_para)
        self.char_style, self.char_plus = self._section(box, "Text level formatting",
                                                         self.reset_char_style,
                                                         self.clear_char)
        box.pack_start(Gtk.Separator(), False, False, 4)
        clear = Gtk.Button(label="Clear All")
        clear.set_halign(Gtk.Align.START)
        clear.connect("clicked", lambda *_: (self.clear_all(), self.schedule(150)))
        box.pack_start(clear, False, False, 0)
        self.pack_start(box, True, True, 0)
        win.engine.connect("state-changed", self._state)

    def _section(self, box, title, reset, clear):
        h = Gtk.Label(xalign=0)
        h.set_markup("<b>%s</b>" % title)
        box.pack_start(h, False, False, 0)
        row = Gtk.Box(spacing=4)
        style = Gtk.Entry()
        style.set_editable(False)
        style.set_can_focus(False)
        row.pack_start(style, True, True, 0)
        b = self._icon_button("cmd/sc_resetattributes", "Reset to Normal", reset)
        row.pack_start(b, False, False, 0)
        box.pack_start(row, False, False, 0)
        row2 = Gtk.Box(spacing=4)
        plus = Gtk.Label(xalign=0, yalign=0)
        plus.set_line_wrap(True)
        plus.set_max_width_chars(30)
        plus.set_ellipsize(Pango.EllipsizeMode.NONE)
        frame = Gtk.Frame()
        frame.add(plus)
        plus.set_margin_start(4)
        plus.set_margin_top(2)
        plus.set_margin_bottom(2)
        row2.pack_start(frame, True, True, 0)
        row2.pack_start(self._icon_button("cmd/sc_resetattributes", "Clear Formatting", clear),
                        False, False, 0)
        box.pack_start(row2, False, False, 0)
        return style, plus

    def _icon_button(self, icon, tip, cb):
        from . import icons
        b = Gtk.Button()
        b.add(icons.image(icon, 16))
        b.set_tooltip_text(tip)
        b.set_relief(Gtk.ReliefStyle.NONE)
        b.connect("clicked", lambda *_: (cb(), self.schedule(150)))
        return b

    @property
    def ed(self):
        return getattr(self.win.engine, "ed", None)

    def _state(self, eng, key, value):
        if self.get_mapped():
            self.schedule()

    def schedule(self, delay=250):
        if self._timer:
            GLib.source_remove(self._timer)
        self._timer = GLib.timeout_add(delay, self.refresh)

    def on_shown(self):
        self.refresh()

    def refresh(self):
        self._timer = None
        ed = self.ed
        if ed is None:
            return False
        st = ed.state() or {}
        styles = _style_ids(ed)
        cs = st.get("char_style_id") or ""
        cname = styles[cs][1] if cs in styles else "Default Paragraph Font"
        para, text = direct_formatting(ed)
        self.para_style.set_text(st.get("style") or "Normal")
        self.char_style.set_text(cname)
        self.para_plus.set_markup("Plus: " + html.escape(", ".join(para) if para else "<none>"))
        self.char_plus.set_markup("Plus: " + html.escape(", ".join(t for t in text if t) if text else "<none>"))
        return False

    def _after(self):
        self.win.engine.view.after_edit()

    def reset_para_style(self):
        self.win.actions.apply_style("Normal")

    def clear_para(self):
        clear_para(self.ed)
        self._after()

    def reset_char_style(self):
        self.ed.set_char_style("")
        self._after()

    def clear_char(self):
        clear_char(self.ed)
        self._after()

    def clear_all(self):
        ed = self.ed
        ed.begin_group("Clear All")
        try:
            clear_char(ed)
            ed.set_char_style("")
            clear_para(ed)
        finally:
            ed.end_group()
        self.win.actions.apply_style("Normal")
        self._after()


# ------------------------------------------------------------ manage styles
def manage_styles(win, page=0):
    from .actions import word_style
    ed = getattr(win.engine, "ed", None)
    if ed is None:
        return
    d = FDialog(win, "Manage Styles")
    nb = Gtk.Notebook()
    # --- Edit
    edit = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, margin=8)
    sort = Gtk.ComboBoxText()
    for t in ("As Recommended", "Alphabetical", "Based On", "By type"):
        sort.append_text(t)
    sort.set_active(0)
    row = Gtk.Box(spacing=6)
    row.pack_start(Gtk.Label(label="Sort order:"), False, False, 0)
    row.pack_start(sort, False, False, 0)
    used = Gtk.CheckButton(label="Show recommended styles only")
    row.pack_start(used, False, False, 12)
    edit.pack_start(row, False, False, 0)
    store = Gtk.ListStore(str, str, str, str, bool)     # name, id, kind, based on, custom
    tv = Gtk.TreeView(model=store)
    tv.set_headers_visible(False)
    tv.append_column(Gtk.TreeViewColumn("", Gtk.CellRendererText(), text=0))
    sw = Gtk.ScrolledWindow()
    sw.set_size_request(440, 220)
    sw.add(tv)
    edit.pack_start(sw, True, True, 0)
    preview = Gtk.Label(xalign=0)
    preview.set_line_wrap(True)
    preview.set_max_width_chars(60)
    pf = Gtk.Frame(label="Preview")
    pf.add(preview)
    edit.pack_start(pf, False, False, 0)
    bb = Gtk.Box(spacing=6)
    b_mod = Gtk.Button(label="Modify...")
    b_del = Gtk.Button(label="Delete")
    b_new = Gtk.Button(label="New Style...")
    for b in (b_mod, b_del):
        bb.pack_start(b, False, False, 0)
    bb.pack_end(b_new, False, False, 0)
    edit.pack_start(bb, False, False, 0)
    from .panes import PREFERRED

    def fill():
        store.clear()
        rows = []
        names = {s[0]: s[1] for s in ed.style_list()}
        for sid, name, kind, based, _nxt, custom, _auto, gallery in ed.style_list():
            if kind not in ("paragraph", "character"):
                continue
            wn = word_style(name)
            if used.get_active() and wn not in PREFERRED and not custom:
                continue
            if not (custom or gallery or wn in PREFERRED or (kind == "paragraph" and ed.count_style_instances(sid))):
                continue
            rows.append((wn, sid, kind, word_style(names.get(based, "")) if based else "", custom))
        mode = sort.get_active()
        order = {n: i for i, n in enumerate(PREFERRED)}
        if mode == 0:
            rows.sort(key=lambda r: (order.get(r[0], 999), r[0].lower()))
        elif mode == 1:
            rows.sort(key=lambda r: r[0].lower())
        elif mode == 2:
            rows.sort(key=lambda r: (r[3].lower(), r[0].lower()))
        else:
            rows.sort(key=lambda r: (r[2], r[0].lower()))
        for r in rows:
            store.append(list(r))
        if len(store):
            tv.get_selection().select_path(Gtk.TreePath(0))

    def current():
        model, it = tv.get_selection().get_selected()
        return tuple(model[it]) if it else None

    def show_preview(*_):
        cur = current()
        if not cur:
            return
        wn, sid, kind, parent, custom = cur
        rv = ed.style_run_values(sid)
        pf.set_label("Preview of %s" % wn)
        size = float(rv.get("size") or 11)
        font = rv.get("font") or "Sans"
        bold = " weight='bold'" if rv.get("bold") else ""
        italic = " style='italic'" if rv.get("italic") else ""
        desc = ["Font: %s, %g pt" % (font, size)]
        if parent:
            desc.append("Based on: %s" % parent)
        preview.set_markup("<span font_family='%s' size='%dpt'%s%s>AaBbCcEeGgHhIiJj</span>\n"
                           "<small>%s</small>" % (html.escape(font), min(20, size), bold, italic,
                                                  html.escape(", ".join(desc))))
        b_del.set_sensitive(custom)

    tv.get_selection().connect("changed", show_preview)
    sort.connect("changed", lambda *_: fill())
    used.connect("toggled", lambda *_: fill())

    def modify(*_):
        cur = current()
        if cur:
            win.dialogs.modify_style(cur[0])
            fill()

    def delete(*_):
        cur = current()
        if not cur:
            return
        if win.dialogs.confirm("Do you want to delete style %s from the document?" % cur[0],
                               yes="Yes", no="No"):
            if not ed.delete_style(cur[1]):
                win.dialogs.message("The style couldn't be deleted.")
            win.engine.view.after_edit()
            fill()

    def new(*_):
        win.dialogs.new_style()
        fill()
    b_mod.connect("clicked", modify)
    b_del.connect("clicked", delete)
    b_new.connect("clicked", new)
    tv.connect("row-activated", modify)
    fill()
    nb.append_page(edit, Gtk.Label(label="Edit"))

    # --- Set Defaults (the Normal style)
    ids = {n: i for i, n in ed.paragraph_styles()}
    nid = ids.get("Normal", "Normal")
    rv = ed.style_run_values(nid)
    pv = ed.style_para_values(nid)
    defaults = Gtk.Grid(row_spacing=8, column_spacing=10, margin=10)
    hdr = Gtk.Label(xalign=0)
    hdr.set_markup("<b>Font</b>")
    defaults.attach(hdr, 0, 0, 4, 1)
    font = Gtk.ComboBoxText.new_with_entry()
    for f in win.engine.fonts()[:400]:
        font.append_text(f)
    font.get_child().set_text(rv.get("font") or "")
    size = Gtk.SpinButton.new_with_range(1, 400, 0.5)
    size.set_value(float(rv.get("size") or 11))
    defaults.attach(Gtk.Label(label="Font:", xalign=0), 0, 1, 1, 1)
    defaults.attach(font, 1, 1, 1, 1)
    defaults.attach(Gtk.Label(label="Size:", xalign=0), 2, 1, 1, 1)
    defaults.attach(size, 3, 1, 1, 1)
    hdr2 = Gtk.Label(xalign=0)
    hdr2.set_markup("<b>Paragraph Spacing</b>")
    defaults.attach(hdr2, 0, 2, 4, 1)
    before = Gtk.SpinButton.new_with_range(0, 1584, 1)
    before.set_value(round((pv.get("before") or 0) / 20.0))
    after = Gtk.SpinButton.new_with_range(0, 1584, 1)
    after.set_value(round((pv.get("after") or 0) / 20.0))
    line = Gtk.ComboBoxText()
    lines = [("Single", 240), ("1.08", 259), ("1.15", 276), ("1.5 lines", 360), ("Double", 480)]
    for t, _v in lines:
        line.append_text(t)
    cur_h = pv.get("line", 240) if pv.get("line_rule", "auto") == "auto" else 240
    line.set_active(min(range(len(lines)), key=lambda i: abs(lines[i][1] - cur_h)))
    defaults.attach(Gtk.Label(label="Before:", xalign=0), 0, 3, 1, 1)
    defaults.attach(before, 1, 3, 1, 1)
    defaults.attach(Gtk.Label(label="After:", xalign=0), 2, 3, 1, 1)
    defaults.attach(after, 3, 3, 1, 1)
    defaults.attach(Gtk.Label(label="Line spacing:", xalign=0), 0, 4, 1, 1)
    defaults.attach(line, 1, 4, 1, 1)
    scope_doc = Gtk.RadioButton(label="Only in this document")
    scope_tpl = Gtk.RadioButton(label="New documents based on this template",
                                group=scope_doc)
    defaults.attach(scope_doc, 0, 5, 4, 1)
    defaults.attach(scope_tpl, 0, 6, 4, 1)
    nb.append_page(defaults, Gtk.Label(label="Set Defaults"))
    d.add(nb, expand=True)
    nb.show_all()
    nb.set_current_page(page)
    first = (rv.get("font") or "", float(rv.get("size") or 11), before.get_value(), after.get_value(),
             line.get_active())
    r = d.ask()
    now = (font.get_child().get_text().strip(), size.get_value(), before.get_value(), after.get_value(),
           line.get_active())
    if r == Gtk.ResponseType.OK and (nb.get_current_page() == 1 or now != first):

        def apply(t, sid):
            run = [("w:sz", [("w:val", str(int(round(now[1] * 2))))]),
                   ("w:szCs", [("w:val", str(int(round(now[1] * 2))))])]
            if now[0]:
                run.append(("w:rFonts", [("w:ascii", now[0]), ("w:hAnsi", now[0]), ("w:cs", now[0])]))
            t.style_apply_run(sid, run)
            t.style_apply_para(sid, [("w:spacing", [("w:before", str(int(now[2] * 20))),
                                                    ("w:after", str(int(now[3] * 20))),
                                                    ("w:line", str(lines[now[4]][1])),
                                                    ("w:lineRule", "auto")])])
        ed.begin_group("Set Defaults")
        try:
            apply(ed, nid)
        finally:
            ed.end_group()
        if scope_tpl.get_active():
            try:
                from .native import edit_normal_template
                edit_normal_template(win.app, lambda t: apply(t, {n: i for i, n in t.paragraph_styles()}
                                                              .get("Normal", "Normal")))
            except Exception as e:
                print("defaults:", e)
        win.engine.view.after_edit()
        win.design_changed()
    d.done()
