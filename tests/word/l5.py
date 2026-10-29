import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
from folio.native import refs as NR
def idx_text(kind):
    """(field code, result text) of the first table of contents / figures / index."""
    for _d, code, result in fields():
        c = code.strip().upper()
        k = "INDEX" if c.startswith("INDEX") else ("TOF" if c.startswith("TOC") and ("\\C" in c or "\\A" in c) else ("TOC" if c.startswith("TOC") else None))
        if k == kind:
            return code, result
    return None, ""
def toc():
    fresh(); yield 0.3
    T("\nAlpha\nBeta\nGamma"); yield 0.5
    for i, st in ((2, "Heading 1"), (3, "Heading 2"), (4, "Heading 1")):
        para_rng(i - 1).select(); win.actions.apply_style(st)
    K("ctrl+Home"); yield 0.3
    GLib.idle_add(lambda: (win.dialogs.toc_dialog(), False)[1]); yield 1.2
    d = dlg("Table of Contents")
    check("TOC dialog", bool(d))
    shot("l5_toc")
    labs = [w.get_label() for w in find_widget(d[0], lambda w: isinstance(w, Gtk.CheckButton))]
    check("TOC checkboxes", all(any(x in (l or "") for l in labs) for x in ("Show page numbers", "Right align", "hyperlinks")), labs)
    btns = [w.get_label() for w in find_widget(d[0], lambda w: isinstance(w, Gtk.Button) and not isinstance(w, Gtk.CheckButton))]
    check("Options and Modify", "_Options..." in btns and "_Modify..." in btns, btns)
    cb = [w for w in find_widget(d[0], lambda w: isinstance(w, Gtk.ComboBoxText))]
    lead = [c for c in cb if any(r[0] == "--------" for r in c.get_model())]
    check("tab leader choice", bool(lead))
    lead[0].set_active([r[0] for r in lead[0].get_model()].index("--------"))   # dashes
    respond("Table of Contents"); yield 1.5
    x, t = idx_text("TOC")
    note("toc text", repr(t))
    check("TOC inserted with entries", "Alpha" in t and "Beta" in t and "Gamma" in t, t)
    dx = part_xml("word/document.xml")
    check("dash leader", 'w:leader="hyphen"' in dx, dx[dx.find("<w:body>"):][:300])
    # reopen: replaces the same TOC
    GLib.idle_add(lambda: (win.dialogs.toc_dialog(), False)[1]); yield 1.2
    d = dlg("Table of Contents")
    for w in find_widget(d[0], lambda w: isinstance(w, Gtk.CheckButton)):
        if "Show page numbers" in (w.get_label() or ""): w.set_active(False)
    respond("Table of Contents"); yield 1.0
    # "Do you want to replace the selected table of contents?" - Yes
    respond("Folio Page", Gtk.ResponseType.YES)
    yield 1.5
    check("one TOC only", len(NR._toc_fields(win)) == 1, NR._toc_fields(win))
    x, t = idx_text("TOC")
    check("no page numbers", not any(ch.isdigit() for ch in t), repr(t))
    # options dialog
    GLib.idle_add(lambda: (win.dialogs.toc_dialog(), False)[1]); yield 1.2
    d = dlg("Table of Contents")
    ob = [w for w in find_widget(d[0], lambda w: isinstance(w, Gtk.Button) and w.get_label() == "_Options...")][0]
    GLib.idle_add(lambda: (ob.clicked(), False)[1]); yield 1.2
    check("TOC Options dialog", bool(dlg("Table of Contents Options")))
    shot("l5_tocopt")
    respond("Table of Contents Options", Gtk.ResponseType.CANCEL); yield 0.5
    respond("Table of Contents", Gtk.ResponseType.CANCEL); yield 0.5
def tof():
    fresh(); yield 0.3
    T("x"); yield 0.3
    E.ed.insert_caption("Figure", ": First picture", True, "ARABIC", False); E.view.after_edit(); yield 0.5
    K("ctrl+End"); T("\n"); yield 0.8
    E.ed.insert_caption("Figure", ": Second picture", True, "ARABIC", False); E.view.after_edit(); yield 0.5
    K("ctrl+Home"); T("\n"); K("ctrl+Home"); yield 0.3
    GLib.idle_add(lambda: (win.dialogs.table_of_figures(), False)[1]); yield 1.2
    d = dlg("Table of Figures")
    check("TOF dialog", bool(d))
    shot("l5_tof")
    respond("Table of Figures"); yield 1.5
    close_dialogs(); yield 0.3
    x, t = idx_text("TOF")
    note("tof", repr(t))
    check("TOF has entries", "First picture" in t and "Second picture" in t, t)
def index():
    fresh(); yield 0.3
    T("apple banana cherry"); yield 0.3
    K("ctrl+Home"); K("ctrl+shift+Right"); yield 0.3
    E.ed.insert_code_field(NR.xe_instr("Apple")); E.view.after_edit(); yield 0.3
    K("ctrl+End"); T("\n"); yield 0.3
    GLib.idle_add(lambda: (win.dialogs.insert_index(), False)[1]); yield 1.2
    d = dlg("Index")
    check("Index dialog", bool(d))
    shot("l5_index")
    btns = [w.get_label() for w in find_widget(d[0], lambda w: isinstance(w, Gtk.Button))]
    check("Index buttons", all(x in btns for x in ("Mar_k Entry...", "A_utoMark...", "_Modify...")), btns)
    for w in find_widget(d[0], lambda w: isinstance(w, Gtk.CheckButton)):
        if "Right align" in (w.get_label() or ""): w.set_active(True)
    respond("Index"); yield 1.5
    x, t = idx_text("INDEX")
    note("index", repr(t))
    check("Index has entry", "Apple" in t, t)
run_scenarios(toc, tof, index)
