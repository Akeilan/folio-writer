exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
def pos():
    c = vc(); r = c.getText().createTextCursorByRange(c.getEnd()); r.gotoStartOfParagraph(True)
    return repr(r.getString())
def nav():
    fresh(); yield 0.4
    T("one two three four\nsecond paragraph here\nthird para"); yield 1.0
    K("ctrl+Home"); yield 0.3; note("after ctrl+home", pos())
    K("ctrl+Down"); yield 0.4; note("after ctrl+down", pos() + " page/line y=%s" % vc().getPosition().Y)
    K("Down"); yield 0.4; note("after down", pos())
    K("ctrl+Up"); yield 0.4; note("after ctrl+up", pos())
    K("End"); yield 0.3; note("after End", pos())
    K("shift+Home"); yield 0.3; note("shift+home sel", repr(sel()))
    K("ctrl+End"); yield 0.4; note("after ctrl+end", pos() + " para=" + repr(vc().getText().createTextCursorByRange(vc().getEnd()).getString()))
    K("ctrl+shift+Home"); yield 0.4; note("ctrl+shift+home sel", repr(sel())[:80])
    K("Right"); yield 0.3
    K("Home"); yield 0.2; K("ctrl+Delete"); yield 0.5; note("ctrl+delete text", repr(text()))
    K("ctrl+z"); yield 0.4
    K("ctrl+End"); yield 0.3; K("ctrl+shift+Up"); yield 0.4; note("ctrl+shift+up sel", repr(sel()))
def fmt():
    fresh(); yield 0.4
    T("plain "); K("ctrl+u"); T("under"); K("ctrl+u"); T(" end"); yield 0.8
    en = paras()[0].createEnumeration()
    while en.hasMoreElements():
        r = en.nextElement(); note("portion", (r.getString(), r.CharWeight, r.CharUnderline))
    fresh(); yield 0.3
    T("hello world"); K("ctrl+shift+Left"); yield 0.3
    K("shift+F3"); yield 0.5; note("shift+f3 1", repr(text()))
    K("shift+F3"); yield 0.5; note("shift+f3 2", repr(text()))
def lists():
    fresh(); yield 0.4
    T("1. first"); yield 0.5; note("before enter", repr(text()))
    K("Return"); yield 0.6
    for p in paras(): note("p", (p.getString(), p.NumberingIsNumber, p.ListLabelString, p.NumberingStyleName, p.ParaStyleName))
    T("second"); yield 0.3
    K("Home"); K("Tab"); yield 0.5
    for p in paras(): note("p after tab", (p.getString(), p.NumberingLevel, p.ListLabelString))
    shot("w1b_list")
    fresh(); yield 0.4
    T("a) item"); K("Return"); yield 0.6
    for p in paras(): note("a)", (p.getString(), p.NumberingIsNumber, p.ListLabelString))
    fresh(); yield 0.4
    T("---"); K("Return"); yield 0.7
    for p in paras(): note("---", (p.getString(), p.BottomBorder.OuterLineWidth, p.BottomBorder.LineWidth))
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
    en = paras()[0].createEnumeration()
    while en.hasMoreElements():
        r = en.nextElement(); note("fmt portion", (r.getString(), r.CharWeight))
    K("ctrl+alt+v"); yield 1.2
    note("toplevels", [(w.get_title(), w.get_visible()) for w in Gtk.Window.list_toplevels() if w.get_title()])
    shot("w1b_pastespecial")
    K("Escape"); yield 0.4
    focus(); K("ctrl+alt+m"); yield 1.2
    shot("w1b_comment")
    note("comment fields", [f.getPropertyValue("Content") if f.supportsService("com.sun.star.text.textfield.Annotation") else f.getImplementationName() for f in iter_fields()])
def iter_fields():
    en = M().getTextFields().createEnumeration(); out = []
    while en.hasMoreElements(): out.append(en.nextElement())
    return out
run_scenarios(nav, fmt, lists, clip)
