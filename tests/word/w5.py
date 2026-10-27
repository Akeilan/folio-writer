exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
def files():
    fresh(); yield 0.3
    T("Save me"); yield 0.3
    K("ctrl+s"); yield 1.5
    note("ctrl+s on new doc", ([d.get_title() for d in dialogs_open()], win.backstage.get_visible() if hasattr(win.backstage, "get_visible") else getattr(win.backstage, "is_open", None)))
    shot("w5_ctrls")
    close_dialogs(); K("Escape"); yield 0.6
    focus(); K("F12"); yield 1.5
    note("F12", [d.get_title() for d in dialogs_open()])
    shot("w5_f12")
    close_dialogs(); K("Escape"); yield 0.6
    focus(); K("ctrl+o"); yield 1.5
    note("ctrl+o", [d.get_title() for d in dialogs_open()])
    shot("w5_ctrlo")
    close_dialogs(); K("Escape"); yield 0.6
    focus(); K("ctrl+p"); yield 2.5
    shot("w5_ctrlp")
    K("Escape"); yield 0.8
    shot("w5_after_esc")
    focus(); K("ctrl+n"); yield 3.0
    note("windows after ctrl+n", len(app.windows))
    if len(app.windows) > 1:
        w2 = app.windows[-1]; K("ctrl+w"); yield 1.5
        note("windows after ctrl+w", len(app.windows))
    focus(); yield 0.3
def findrep():
    fresh(); yield 0.3
    T("cat dog cat bird cat"); yield 0.4
    focus(); K("ctrl+f"); yield 1.0
    T("cat"); yield 1.2
    shot("w5_navsearch")
    note("nav search result", [w.get_text() for w in find_widget(win, lambda w: isinstance(w, Gtk.Label) and "result" in (w.get_text() or "").lower())])
    K("Escape"); focus(); yield 0.3
    K("ctrl+h"); yield 1.2
    d = dlg("Replace")
    ents = find_widget(d[0], lambda w: isinstance(w, Gtk.Entry)) if d else []
    note("replace entries", len(ents))
    if len(ents) >= 2:
        ents[0].set_text("cat"); ents[1].set_text("fox")
        btn = find_widget(d[0], lambda w: isinstance(w, Gtk.Button) and "Replace All" in (w.get_label() or "").replace("_", ""))
        if btn: GLib.idle_add(lambda: (btn[0].clicked(), False)[1])
        yield 1.2
        note("after replace all dialogs", [x.get_title() for x in dialogs_open()])
        shot("w5_replaceall")
        close_dialogs(); yield 0.5
    check("Replace All replaced 3", text().count("fox") == 3, repr(text()))
def views():
    fresh(); yield 0.3
    for h in ("Alpha", "Beta"):
        T(h); K("ctrl+alt+1"); K("Return"); T("Body under " + h); K("Return")
    yield 0.6
    for lab in ("Read Mode", "Web Layout", "Outline", "Draft", "Print Layout"):
        rib("View", lab); yield 1.5
        shot("w5_view_" + lab.replace(" ", ""))
        if lab == "Read Mode":
            K("Escape"); yield 1.0
            shot("w5_view_ReadMode_esc")
    rib("View", "Navigation Pane"); yield 1.0
    shot("w5_navpane")
def painter():
    fresh(); yield 0.3
    T("source target"); docapi.controller(M()).select(find("source")); K("ctrl+b"); yield 0.3
    rib("Home", "Format Painter"); yield 0.6
    # now drag-select 'target' with mouse
    c = vc(); c.gotoRange(find("target").getStart(), False); yield 0.3
    x0, y0, w, h = win._follow_rect
    c.gotoRange(find("target").getEnd(), False); yield 0.3
    x1 = win._follow_rect[0]
    a = doc_screen(x0 + 10, y0 + h / 2); b = doc_screen(x1 - 10, y0 + h / 2)
    X("mousemove", *a); X("mousedown", 1)
    for i in range(1, 6): X("mousemove", int(a[0] + (b[0] - a[0]) * i / 5), a[1]); time.sleep(0.05)
    X("mouseup", 1); yield 1.0
    check("format painter applies bold to dragged text", find("target").CharWeight > 100, find("target").CharWeight)
    # paste options button after paste
    docapi.controller(M()).select(find("source")); K("ctrl+c"); yield 0.4
    K("End"); K("ctrl+v"); yield 1.5
    shot("w5_pasteopts")
def clicktype():
    fresh(); yield 0.3
    T("Top line"); yield 0.4
    c = vc(); c.gotoStart(False); yield 0.3
    x0, y0, w, h = win._follow_rect
    sx, sy = doc_screen(x0 + 4000, y0 + 3000)
    X("mousemove", sx, sy); X("click", "--repeat", 2, "--delay", 80, 1); yield 1.0
    T("Clicked here"); yield 0.6
    note("click and type paras", para_texts())
    shot("w5_clicktype")
def undo_drop():
    fresh(); yield 0.3
    T("one "); yield 0.6; T("two "); yield 0.6; K("ctrl+b"); T("three"); yield 0.6
    for i in range(3):
        K("ctrl+z"); yield 0.4; note("undo %d" % i, repr(text()))
def symbols():
    fresh(); yield 0.3
    rib("Insert", "Symbol"); yield 1.2
    shot("w5_symbol")
    K("Escape"); yield 0.3
    focus(); T("x"); K("alt+0177") ; yield 0.5
    note("alt code", repr(text()))
    fresh(); yield 0.3
    T("00e9"); K("alt+x"); yield 0.6
    check("alt+x converts unicode hex", text() == "é", repr(text()))
run_scenarios(findrep, views, painter, clicktype, undo_drop, symbols)
