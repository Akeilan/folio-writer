import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
def opendlg(fn, title, wait=1.2):
    GLib.idle_add(lambda: (fn(), False)[1])
    return title
def labels_of(d):
    out = []
    for w in find_widget(d, lambda w: isinstance(w, (Gtk.Label, Gtk.Button))):
        t = w.get_label() if isinstance(w, Gtk.Button) else w.get_text()
        if t: out.append(t.replace("_", ""))
    return out
def hyperlink():
    fresh(); yield 0.3
    GLib.idle_add(lambda: (win.dialogs.hyperlink(), False)[1]); yield 1.2
    d = dlg("Hyperlink")[0]
    L = labels_of(d)
    for x in ("Create New\nDocument", "Bookmark...", "Target Frame...", "Recently used e-mail addresses:"):
        check("hyperlink has " + x.replace("\n", " "), x in L, "")
    shot("l9_link")
    close_dialogs(); yield 0.4
def table():
    fresh(); yield 0.3
    GLib.idle_add(lambda: (win.dialogs.insert_table_dialog(), False)[1]); yield 1.0
    d = dlg("Insert Table")[0]
    rb = {w.get_label(): w for w in find_widget(d, lambda w: isinstance(w, Gtk.RadioButton))}
    check("AutoFit options", "Auto_Fit to contents" in rb and "AutoFit to win_dow" in rb, list(rb))
    rb["AutoFit to win_dow"].set_active(True)
    respond("Insert Table"); yield 1.5
    cell_rng("A1").caret_to_start()
    tp = dict(E.ed.table_props())
    note("table props", tp)
    check("AutoFit to window (100% width)", tp.get("width") == (5000, "pct"), tp.get("width"))
def field():
    fresh(); yield 0.3
    GLib.idle_add(lambda: (win.dialogs.field_dialog(), False)[1]); yield 1.2
    d = dlg("Field")[0]
    shot("l9_field")
    tv = find_widget(d, lambda w: isinstance(w, Gtk.TreeView))[0]
    names = [r[0] for r in tv.get_model()]
    check("field list grew", "Fillin" in names and "UserName" in names and "Seq" in names, names)
    for i, r in enumerate(tv.get_model()):
        if r[0] == "Page": tv.get_selection().select_path(Gtk.TreePath(i))
    yield 0.4
    combos = find_widget(d, lambda w: isinstance(w, Gtk.ComboBoxText))
    fmtc = [c for c in combos if c.get_active_text() == "1, 2, 3, ..."]
    check("Page has formats", bool(fmtc), [c.get_active_text() for c in combos])
    if fmtc: fmtc[0].set_active(4)
    ent = [w for w in find_widget(d, lambda w: isinstance(w, Gtk.Entry)) if "PAGE" in (w.get_text() or "")]
    check("field code shown", bool(ent) and "ROMAN" in ent[0].get_text(), [e.get_text() for e in find_widget(d, lambda w: isinstance(w, Gtk.Entry))])
    respond("Field"); yield 1.0
    check("Roman page field", "I" in text(), repr(text()))
def sort():
    fresh(); yield 0.3
    T("b\t2\na\t3\nc\t1"); yield 0.8
    K("ctrl+a"); yield 0.6
    note("sel before sort", repr(sel()))
    GLib.idle_add(lambda: (win.dialogs.sort_dialog(), False)[1]); yield 1.2
    d = dlg("Sort")[0]
    shot("l9_sort")
    combos = find_widget(d, lambda w: isinstance(w, Gtk.ComboBoxText))
    models = [[r[0] for r in c.get_model()] for c in combos]
    check("sort offers fields", any("Field 2" in mm for mm in models), models)
    respond("Sort", Gtk.ResponseType.CANCEL); yield 0.5
    from folio import sortdlg
    K("ctrl+a"); yield 0.5
    sortdlg.sort_native(win, [(2, 1, True)], False, {"sep": "\t"}); yield 0.8
    check("sorted by field 2", [p.lower() for p in para_texts()[:3]] == ["c\t1", "b\t2", "a\t3"], para_texts())
def caption():
    fresh(); yield 0.3
    T("x"); yield 0.3
    GLib.idle_add(lambda: (win.dialogs.caption(), False)[1]); yield 1.2
    d = dlg("Caption")[0]
    L = labels_of(d)
    for x in ("Delete Label", "Numbering...", "AutoCaption..."):
        check("caption has " + x, x in L, "")
    shot("l9_caption")
    respond("Caption"); yield 1.0
    check("caption inserted", "Figure 1" in text(), repr(text()))
def xref():
    fresh(); yield 0.3
    T("Target here"); yield 0.3
    para_rng(0).select(); E.ed.add_bookmark("Target1"); E.view.after_edit(); yield 0.3
    check("bookmark added", "Target1" in E.ed.bookmark_names(), E.ed.bookmark_names())
    K("ctrl+End"); T("\nSee "); yield 0.8
    GLib.idle_add(lambda: (win.dialogs.cross_reference(), False)[1]); yield 1.2
    d = dlg("Cross-reference")[0]
    combos = find_widget(d, lambda w: isinstance(w, Gtk.ComboBoxText))
    note("xref combos", [[r[0] for r in c.get_model()] for c in combos], )
    rt = [c for c in combos if any(r[0] == "Bookmark" for r in c.get_model())][0]
    rt.set_active([r[0] for r in rt.get_model()].index("Bookmark"))
    yield 0.4
    chk = {w.get_label(): w for w in find_widget(d, lambda w: isinstance(w, Gtk.CheckButton))}
    check("xref options", "Insert as _hyperlink" in chk and "Include above/_below" in chk, list(chk))
    respond("Cross-reference"); yield 1.0
    close_dialogs(); yield 0.3
    p = top_paras()[1]
    refs = [c for _d, c, _r in fields() if c.split()[:2] == ["REF", "Target1"]]
    check("reference text + hyperlink (REF Target1 \\h)", "Target here" in ptext(p) and refs and "\\h" in refs[0], (ptext(p), fields()))
def counts():
    fresh(); yield 0.3
    set_text("one two three\nfour five"); yield 0.5
    n = E.ed.stats(False)["lines"]
    check("count lines", n == 2, n)
def borders():
    fresh(); yield 0.3
    T("para"); yield 0.3
    GLib.idle_add(lambda: (win.dialogs.borders_dialog(), False)[1]); yield 1.2
    d = dlg("Borders and Shading")[0]
    shot("l9_borders")
    rb = {w.get_label(): w for w in find_widget(d, lambda w: isinstance(w, Gtk.RadioButton))}
    check("3-D and Custom", "3-_D" in rb and "C_ustom" in rb, list(rb))
    tg = {}
    for w in find_widget(d, lambda w: isinstance(w, Gtk.ToggleButton) and not isinstance(w, Gtk.CheckButton)):
        if w.get_label() in ("Top", "Bottom", "Left", "Right"): tg.setdefault(w.get_label(), w)
    tg["Bottom"].set_active(True)
    respond("Borders and Shading"); yield 1.0
    check("custom bottom border", bool(border("bottom", 0)) and not border("top", 0), pv(0).get("borders"))
def options():
    GLib.idle_add(lambda: (win.dialogs.options(), False)[1] if hasattr(win.dialogs, "options") else (win.run("options"), False)[1]); yield 1.5
    d = dlg("Options")
    if d:
        st = find_widget(d[0], lambda w: isinstance(w, Gtk.Stack))[0]
        names = [st.child_get_property(c, "title") for c in st.get_children()]
        check("Options pages", all(x in names for x in ("Language", "Accessibility", "Quick Access Toolbar")), names)
        st.set_visible_child_name("quick access toolbar"); yield 0.5
        shot("l9_qat")
    else:
        check("Options opened", False)
    close_dialogs(); yield 0.4
def zoom():
    GLib.idle_add(lambda: (win.dialogs.zoom_dialog(), False)[1]); yield 1.0
    d = dlg("Zoom")[0]
    rb = {w.get_label(): w for w in find_widget(d, lambda w: isinstance(w, Gtk.RadioButton))}
    check("Many pages", "_Many pages:" in rb, list(rb))
    rb["_Many pages:"].set_active(True)
    respond("Zoom"); yield 1.5
    shot("l9_many")
    note("page rects", win.engine.page_rects()[:3])
    win.dialogs.zoom_100(); yield 0.5
def envelopes():
    from folio import dlg_mail
    GLib.idle_add(lambda: (dlg_mail.envelopes(win), False)[1]); yield 1.2
    d = dlg("Envelopes")
    check("Envelopes opened", bool(d))
    if d:
        L = labels_of(d[0])
        check("Envelope preview/feed/options", "Preview" in L and "Feed" in L and "Options..." in L, L)
        shot("l9_env")
    close_dialogs(); yield 0.4
run_scenarios(hyperlink, table, field, sort, caption, xref, counts, borders, options, zoom, envelopes)
