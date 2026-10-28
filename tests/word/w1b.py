exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
def where():
    return repr(pos())
def nav():
    fresh(); yield 0.4
    T("one two three four\nsecond paragraph here\nthird para"); yield 1.0
    K("ctrl+Home"); yield 0.3; note("after ctrl+home", where())
    K("ctrl+Down"); yield 0.4; note("after ctrl+down", where() + " caret y=%s" % E.ed.caret_rect()[2])
    K("Down"); yield 0.4; note("after down", where())
    K("ctrl+Up"); yield 0.4; note("after ctrl+up", where())
    K("End"); yield 0.3; note("after End", where())
    K("shift+Home"); yield 0.3; note("shift+home sel", repr(sel()))
    K("ctrl+End"); yield 0.4; note("after ctrl+end", where() + " para=" + repr(caret_para_text()))
    K("ctrl+shift+Home"); yield 0.4; note("ctrl+shift+home sel", repr(sel())[:80])
    K("Right"); yield 0.3
    K("Home"); yield 0.2; K("ctrl+Delete"); yield 0.5; note("ctrl+delete text", repr(text()))
    K("ctrl+z"); yield 0.4
    K("ctrl+End"); yield 0.3; K("ctrl+shift+Up"); yield 0.4; note("ctrl+shift+up sel", repr(sel()))
def fmt():
    fresh(); yield 0.4
    T("plain "); K("ctrl+u"); T("under"); K("ctrl+u"); T(" end"); yield 0.8
    for w in ("plain", "under", "end"):
        f = find(w).run(); note("portion", (w, f["bold"], f["underline"]))
    fresh(); yield 0.3
    T("hello world"); K("ctrl+shift+Left"); yield 0.3
    K("shift+F3"); yield 0.5; note("shift+f3 1", repr(text()))
    K("shift+F3"); yield 0.5; note("shift+f3 2", repr(text()))
def lists():
    fresh(); yield 0.4
    T("1. first"); yield 0.5; note("before enter", repr(text()))
    K("Return"); yield 0.6
    for i, t in enumerate(para_texts()): note("p", (t, is_listed(i), list_label(i), style_of(i)))
    T("second"); yield 0.3
    K("Home"); K("Tab"); yield 0.5
    for i, t in enumerate(para_texts()): note("p after tab", (t, list_level(i), list_label(i)))
    shot("w1b_list")
    fresh(); yield 0.4
    T("a) item"); K("Return"); yield 0.6
    for i, t in enumerate(para_texts()): note("a)", (t, is_listed(i), list_label(i)))
    fresh(); yield 0.4
    T("---"); K("Return"); yield 0.7
    for i, t in enumerate(para_texts()): note("---", (t, border("bottom", i)))
    shot("w1b_rule")
def clip():
    fresh(); yield 0.4
    T("cut me"); yield 0.3
    K("ctrl+a"); yield 0.3; K("ctrl+x"); yield 0.8; note("after cut", repr(text()))
    K("ctrl+v"); yield 1.2; note("after paste", repr(text()))
    K("ctrl+c"); yield 0.3
    T("x"); yield 0.3
    K("ctrl+v"); yield 1.2; note("after paste 2", repr(text()))
    fresh(); yield 0.3
    T("fmt"); K("ctrl+shift+Left"); K("ctrl+b"); yield 0.3
    K("ctrl+shift+c"); yield 0.4; K("End"); T(" tgt"); K("ctrl+shift+Left"); yield 0.3
    K("ctrl+shift+v"); yield 0.6
    for w in ("fmt", "tgt"):
        note("fmt portion", (w, find(w).run()["bold"]))
    K("ctrl+alt+v"); yield 1.2
    note("toplevels", [(w.get_title(), w.get_visible()) for w in Gtk.Window.list_toplevels() if w.get_title()])
    shot("w1b_pastespecial")
    K("Escape"); yield 0.4
    focus(); K("ctrl+alt+m"); yield 1.2
    shot("w1b_comment")
    note("comments", [c["text"] for c in comments()])
run_scenarios(nav, fmt, lists, clip)
