exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())

def at_word(word, nth=0, frac=0.5):
    r = find(word, nth)
    c = vc(); c.gotoRange(r.getStart(), False)
    yield 0.3
    x0, y0, w, h = win._follow_rect
    c.gotoRange(r.getEnd(), False)
    yield 0.3
    x1 = win._follow_rect[0]
    AT["xy"] = doc_screen(x0 + (x1 - x0) * frac, y0 + h / 2)
    AT["line"] = (x0, y0, h)
AT = {}

def setup_text():
    fresh(); yield 0.3
    win.actions.insert_text("Alpha bravo charlie delta echo foxtrot golf hotel.")
    E.command(".uno:InsertPara")
    win.actions.insert_text("Second paragraph with some words in it.")
    E.command(".uno:InsertPara")
    win.actions.insert_text("Thrid paragraph has a speling mistake.")
    yield 0.8

def clicks():
    yield from setup_text()
    yield from at_word("charlie", frac=0.5)
    click(*AT["xy"]); yield 0.5
    c = vc(); r = c.getText().createTextCursorByRange(c.getStart()); r.gotoStartOfParagraph(True)
    check("single click places caret inside word", r.getString().startswith("Alpha bravo ch"), repr(r.getString()))
    click(*AT["xy"], n=2); yield 0.6
    check("double-click selects word + trailing space", sel() in ("charlie ", "charlie"), repr(sel()))
    note("double-click selection", repr(sel()))
    click(*AT["xy"], n=3); yield 0.7
    check("triple-click selects paragraph", (sel() or "").startswith("Alpha") and (sel() or "").rstrip().endswith("hotel."), repr(sel()))
    yield from at_word("Second", frac=0.0)
    lx, ly = AT["xy"]
    click(lx - 40, ly); yield 0.6
    check("click in left margin selects line", (sel() or "").startswith("Second"), repr(sel()))
    click(lx - 40, ly, n=2); yield 0.6
    check("double-click in left margin selects paragraph", (sel() or "").startswith("Second"), repr(sel()))
    click(lx - 40, ly, n=3); yield 0.6
    check("triple-click in left margin selects document", "Thrid" in (sel() or "") and "Alpha" in (sel() or ""), repr(sel())[:40])
    # shift+click extend
    yield from at_word("bravo", frac=0.0)
    a = AT["xy"]
    yield from at_word("echo", frac=1.0)
    b = AT["xy"]
    click(*a); yield 0.4
    click(*b, mods="shift"); yield 0.6
    check("shift+click extends selection", sel() == "bravo charlie delta echo", repr(sel()))
    # ctrl+click selects sentence
    click(*a, mods="ctrl"); yield 0.6
    check("ctrl+click selects sentence", (sel() or "").startswith("Alpha") and (sel() or "").strip().endswith("."), repr(sel()))

def drag():
    yield from setup_text()
    yield from at_word("bravo", frac=0.0); a = AT["xy"]
    yield from at_word("delta", frac=1.0); b = AT["xy"]
    X("mousemove", a[0], a[1]); X("mousedown", 1)
    for i in range(1, 9):
        X("mousemove", int(a[0] + (b[0] - a[0]) * i / 8), a[1]); time.sleep(0.05)
    X("mouseup", 1); yield 0.6
    check("drag selects text", sel() == "bravo charlie delta", repr(sel()))
    # drag and drop the selection to end of paragraph 2
    yield from at_word("charlie", frac=0.5); s = AT["xy"]
    docapi.controller(M()).select(find("bravo charlie delta")); yield 0.4
    yield from at_word("words", frac=1.0); d = AT["xy"]
    docapi.controller(M()).select(find("bravo charlie delta")); yield 0.4
    X("mousemove", s[0], s[1]); X("mousedown", 1)
    for i in range(1, 12):
        X("mousemove", int(s[0] + (d[0] - s[0]) * i / 11), int(s[1] + (d[1] - s[1]) * i / 11)); time.sleep(0.06)
    X("mouseup", 1); yield 1.0
    note("after drag-drop", para_texts())
    check("drag-and-drop moves text", "words bravo charlie delta" in text() or "wordsbravo charlie delta" in text() or "bravo charlie delta in" in text(), para_texts())

def context_menus():
    yield from setup_text()
    yield from at_word("charlie")
    click(*AT["xy"], n=2); yield 0.5
    click(*AT["xy"], button=3); yield 1.0
    labs = menu_labels()
    note("right-click on selection", labs)
    shot("w2_ctx_text")
    for need in ("Cut", "Copy", "Paste", "Font", "Paragraph", "Link", "New Comment"):
        check("context menu has %s" % need, any(need.lower() in l.lower() for l in labs), "")
    K("Escape"); yield 0.4
    yield from at_word("speling")
    click(*AT["xy"], button=3); yield 1.0
    labs = menu_labels()
    note("right-click on misspelling", labs)
    shot("w2_ctx_spell")
    check("misspelling menu offers 'spelling'", any("spelling" == l.strip().lower().replace("_", "") for l in labs), labs[:6])
    check("misspelling menu has Ignore All / Add to Dictionary", any("Ignore" in l for l in labs) and any("Dictionary" in l for l in labs), "")
    K("Escape"); yield 0.4

def minibar():
    yield from setup_text()
    yield from at_word("charlie")
    click(*AT["xy"], n=2); yield 0.6
    X("mousemove", AT["xy"][0] + 5, AT["xy"][1] - 30); yield 1.2
    shot("w2_minibar")
    p = [w for w in popups()]
    note("popups after selection hover", [type(w).__name__ for w in p])
    check("mini toolbar appears near selection", bool(getattr(win, "minibar", None) and win.minibar.get_visible()) if hasattr(win, "minibar") else len(p) > 0, "")

def zoom_scroll():
    yield from setup_text()
    for i in range(40):
        E.command(".uno:InsertPara")
    yield 0.6
    z0 = E.view.get_zoom()
    x, y = widget_center(E.view)
    X("mousemove", x, y); X("keydown", "ctrl"); X("click", 4); X("click", 4); X("keyup", "ctrl"); yield 0.8
    z1 = E.view.get_zoom()
    check("ctrl+wheel zooms in", z1 > z0, (z0, z1))
    win.run("zoom-100") if True else None; yield 0.6
    adj = win.canvas.get_vadjustment(); v0 = adj.get_value()
    X("click", 5); X("click", 5); X("click", 5); yield 0.6
    check("wheel scrolls document", adj.get_value() > v0, (v0, adj.get_value()))
    note("scroll per 3 notches px", adj.get_value() - v0)

def statusbar():
    yield from setup_text()
    st = win.status
    labs = [(w.get_label() if hasattr(w, "get_label") else "") for w in find_widget(st, lambda w: isinstance(w, (Gtk.Button, Gtk.Label)))]
    note("status bar items", [l for l in labs if l])
    wc = find_widget(st, lambda w: isinstance(w, Gtk.Button) and "word" in (w.get_label() or "").lower())
    if wc:
        click(*widget_center(wc[0])); yield 1.0
        check("click word count opens Word Count", any("Word Count" in (d.get_title() or "") for d in dialogs_open()), [d.get_title() for d in dialogs_open()])
        close_dialogs(); yield 0.4
    pg = find_widget(st, lambda w: isinstance(w, Gtk.Button) and "page" in (w.get_label() or "").lower())
    if pg:
        click(*widget_center(pg[0])); yield 1.0
        note("click page number", [d.get_title() for d in dialogs_open()] + ["navpane:%s" % bool(getattr(win, "nav_pane", None))])
        shot("w2_pageclick")
        close_dialogs(); K("Escape"); yield 0.4

def ribbon_ui():
    yield from setup_text()
    docapi.controller(M()).select(find("Second paragraph")); yield 0.3
    # style gallery click Heading 1
    tiles = find_widget(win.ribbon, lambda w: isinstance(w, Gtk.Button) and "Heading 1" in (w.get_tooltip_text() or ""))
    note("heading tiles", len(tiles))
    if tiles:
        click(*widget_center(tiles[0])); yield 0.8
        check("style gallery click applies Heading 1", paras()[1].ParaStyleName == "Heading 1", paras()[1].ParaStyleName)
    # font box
    combos = find_widget(win.ribbon, lambda w: isinstance(w, Gtk.Entry) and w.get_text() in ("Carlito", "Calibri", "Aptos"))
    note("font entries", [c.get_text() for c in combos])
    if combos:
        docapi.controller(M()).select(find("Alpha bravo")); yield 0.3
        click(*widget_center(combos[0]), n=3); yield 0.3
        T("Liberation Serif"); K("Return"); yield 0.8
        check("typing font name in box applies it", find("Alpha").CharFontName == "Liberation Serif", find("Alpha").CharFontName)
    sizes = find_widget(win.ribbon, lambda w: isinstance(w, Gtk.Entry) and w.get_text() in ("11", "12"))
    if sizes:
        docapi.controller(M()).select(find("Alpha bravo")); yield 0.3
        click(*widget_center(sizes[0]), n=3); yield 0.3
        T("15.5"); K("Return"); yield 0.8
        check("typing 15.5 in size box applies it", abs(find("Alpha").CharHeight - 15.5) < 0.01, find("Alpha").CharHeight)
    focus()
    # keytips
    K("alt"); yield 0.8
    shot("w2_keytips")
    K("h"); yield 0.6
    shot("w2_keytips_h")
    K("Escape", "Escape"); yield 0.4
    # hover screentip
    b = find_widget(win.ribbon, lambda w: isinstance(w, Gtk.Button) and (w.get_tooltip_text() or "").startswith("Bold"))
    if b:
        X("mousemove", *widget_center(b[0])); yield 2.0
        shot("w2_screentip")
        X("mousemove", 10, 900); yield 0.3

def ruler():
    yield from setup_text()
    vc().gotoStart(False); yield 0.3
    r = getattr(win, "ruler", None)
    note("ruler", type(r).__name__)
    shot("w2_ruler")

run_scenarios(clicks, drag, context_menus, minibar, zoom_scroll, statusbar, ribbon_ui, ruler)
