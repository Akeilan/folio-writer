"""The Header & Footer tab: Link to Previous, Previous / Next section,
the Page Number Format dialog and Insert Alignment Tab. Double-clicking a
margin to edit the header or footer is the view's own (native/view.py)."""
from gi.repository import Gtk

from .widgets import FDialog, combo, grid


def _where(win):
    """(editor, section, footer, kind) for the header / footer being edited."""
    ed = win.engine.ed
    pg = ed.story_page() if ed.story() == "hf" else None
    if pg is None:
        pg = ed.caret_page()
        return ed, ed.page_section(pg), False, ed.page_hf_kind(pg), None
    return ed, ed.page_section(pg), ed.story_is_footer(), ed.page_hf_kind(pg), pg


def is_linked(win):
    ed, sec, footer, kind, _pg = _where(win)
    return sec > 0 and ed.hf_linked(sec, footer, kind)


def set_link(win, on):
    """Link to Previous: this section shows the previous section's header
    (or footer), or gets its own copy of it to change."""
    ed, sec, footer, kind, pg = _where(win)
    if sec == 0:
        win.status.flash("The first section has nothing before it to link to.")
        return
    if on and not win.dialogs.confirm(
            "Do you want to delete this header/footer and connect to the "
            "header/footer in the previous section?", yes="Yes", no="No"):
        return
    if ed.set_hf_linked(sec, footer, kind, bool(on)):
        if pg is not None:
            ed.edit_header_footer(pg, footer)
        win.engine.view.document_changed()
    win.ribbon.update("folio:hf-link", "true" if is_linked(win) else "false")


def goto_section(win, d):
    """Previous / Next: the header (or footer) of the neighbouring section."""
    ed, sec, footer, _kind, _pg = _where(win)
    k = sec + d
    n = ed.section_count()
    if not 0 <= k < n:
        win.status.flash("There is no %s section." % ("previous" if d < 0 else "next"))
        return
    pages = [i for i in range(ed.page_count()) if ed.page_section(i) == k]
    if not pages:
        return
    pg = pages[0]
    if not ed.page_hf(pg)[1 if footer else 0]:
        ed.ensure_header_footer_kind(k, footer, ed.page_hf_kind(pg))
    ed.edit_header_footer(pg, footer)
    v = win.engine.view
    v.document_changed()
    v.scroll_to_caret()


# ------------------------------------------------------------ page numbers
FORMATS = [("1, 2, 3, ...", "decimal"), ("- 1 -, - 2 -, - 3 -, ...", "numberInDash"),
           ("a, b, c, ...", "lowerLetter"), ("A, B, C, ...", "upperLetter"),
           ("i, ii, iii, ...", "lowerRoman"), ("I, II, III, ...", "upperRoman")]
SEPARATORS = [("- (hyphen)", "hyphen", "-"), (". (period)", "period", "."),
              (": (colon)", "colon", ":"), ("\u2014 (em dash)", "emDash", "\u2014"),
              ("\u2013 (en dash)", "enDash", "\u2013")]


def format_dialog(win):
    """Page Number Format: number format, chapter numbers and where the
    section's numbering starts (w:pgNumType)."""
    ed, sec, _f, _k, _pg = _where(win)
    info = ed.section_info(sec) or {}
    d = FDialog(win, "Page Number Format")
    fmt = combo([f for f, _v in FORMATS], next((i for i, (_f, v) in enumerate(FORMATS)
                                                 if v == info.get("pg_fmt")), 0))
    d.add(grid([["Number _format:", fmt]]))
    chap_now = info.get("pg_chap")
    chap = Gtk.CheckButton.new_with_mnemonic("Include chapter _number")
    heads = combo(["Heading %d" % i for i in range(1, 10)], (chap_now[0] - 1) if chap_now else 0)
    sep = combo([s[0] for s in SEPARATORS],
                next((i for i, s in enumerate(SEPARATORS) if chap_now and s[2] == chap_now[1]), 0))
    cg = grid([["Chapter starts with style:", heads], ["Use separator:", sep]])
    cg.set_margin_start(20)
    chap.connect("toggled", lambda b: cg.set_sensitive(b.get_active()))
    chap.set_active(bool(chap_now))
    cg.set_sensitive(bool(chap_now))
    d.add(chap)
    d.add(cg)
    off = info.get("pg_start")
    d.add(Gtk.Label(label="Page numbering", xalign=0))
    cont = Gtk.RadioButton.new_with_mnemonic(None, "_Continue from previous section")
    start = Gtk.RadioButton.new_with_mnemonic_from_widget(cont, "Start _at:")
    spin = Gtk.SpinButton.new_with_range(0, 9999, 1)
    spin.set_value(off if off is not None else 1)
    start.set_active(off is not None)
    row = Gtk.Box(spacing=6)
    row.pack_start(start, False, False, 0)
    row.pack_start(spin, False, False, 0)
    d.add(cont)
    d.add(row)
    if d.ask() == Gtk.ResponseType.OK:
        label = "Page Number Format"
        ed.begin_group(label)
        try:
            v = FORMATS[max(0, fmt.get_active())][1]
            ed.section_attr(sec, "w:pgNumType", "w:fmt", None if v == "decimal" else v, label)
            ed.section_attr(sec, "w:pgNumType", "w:start",
                            str(int(spin.get_value())) if start.get_active() else None, label)
            on = chap.get_active()
            ed.section_attr(sec, "w:pgNumType", "w:chapStyle",
                            str(heads.get_active() + 1) if on else None, label)
            ed.section_attr(sec, "w:pgNumType", "w:chapSep",
                            SEPARATORS[max(0, sep.get_active())][1] if on else None, label)
        finally:
            ed.end_group()
        win.engine.view.after_edit()
    d.done()


def alignment_tab_dialog(win):
    """Insert Alignment Tab: a tab that lines the text up at the left,
    centre or right of the margin (or indent)."""
    from gi.repository import Gtk
    from .widgets import FDialog, combo, grid, heading
    ed = win.engine.ed
    d = FDialog(win, "Alignment Tab")
    d.add(heading("Alignment"))
    al = Gtk.Box(spacing=12)
    left = Gtk.RadioButton.new_with_mnemonic(None, "_Left")
    center = Gtk.RadioButton.new_with_mnemonic_from_widget(left, "_Center")
    right = Gtk.RadioButton.new_with_mnemonic_from_widget(left, "_Right")
    right.set_active(True)
    for w in (left, center, right):
        al.pack_start(w, False, False, 0)
    d.add(al)
    rel = combo(["Margin", "Indent"], 0)
    d.add(grid([["Ali_gn relative to:", rel]]))
    d.add(heading("Leader"))
    leaders = [("1 None", "none"), ("2 .......", "dot"), ("3 -------", "hyphen"), ("4 ____", "underscore")]
    lead = combo([n for n, _c in leaders], 0)
    d.add(lead)
    if d.ask() == Gtk.ResponseType.OK:
        ps = ed.page_setup(ed.current_section()) or {}
        width = (ps.get("width") or 0) - (ps.get("left") or 0) - (ps.get("right") or 0)
        pv = ed.para_values()
        li = pv.get("ind_left", 0) if rel.get_active() == 1 else 0
        ri = pv.get("ind_right", 0) if rel.get_active() == 1 else 0
        if left.get_active():
            pos, kind = 0, "left"
        elif center.get_active():
            pos, kind = (width - li - ri) // 2, "center"
        else:
            pos, kind = width - li - ri - 1, "right"
        stops = [t for t in pv.get("tabs") or [] if abs(t[0] - pos) > 6]
        stops.append((int(pos), kind, leaders[max(0, lead.get_active())][1]))
        ed.begin_group("Alignment Tab")
        try:
            ed.set_tabs(sorted(stops))
            ed.type_text("\t")
        finally:
            ed.end_group()
        win.engine.view.after_edit()
    d.done()
