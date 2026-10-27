exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
def pos():
    c = vc(); r = c.getText().createTextCursorByRange(c.getEnd()); r.gotoStartOfParagraph(True)
    return repr(r.getString())
def nav():
    fresh(); yield 0.4
    T("one two three"); K("Return"); T("second para"); K("Return"); T("third"); yield 0.8
    note("paras", para_texts())
    K("Home"); yield 0.3; note("Home", pos())
    K("End"); yield 0.3; note("End", pos())
    K("ctrl+Home"); yield 0.3; note("ctrl+Home", pos())
    K("ctrl+Down"); yield 0.3; note("ctrl+Down", pos() + vc().getText().createTextCursorByRange(vc().getEnd()).getString())
    K("End"); yield 0.3; note("End2", pos())
    K("shift+Home"); yield 0.3; note("shift+Home", repr(sel()))
    K("ctrl+Up"); yield 0.3; note("ctrl+Up", pos())
    K("Home"); K("ctrl+Delete"); yield 0.5; note("ctrl+Delete", para_texts())
def copyfmt():
    fresh(); yield 0.4
    T("fmt"); yield 0.3
    K("ctrl+shift+Left"); yield 0.3; note("sel", repr(sel()))
    K("ctrl+b"); yield 0.3; note("text", repr(text()))
    K("ctrl+shift+c"); yield 0.5; note("after ctrl+shift+c", repr(text()))
def lists():
    fresh(); yield 0.4
    T("1. first"); K("Return"); T("second"); yield 0.5
    K("Home"); yield 0.3; K("Tab"); yield 0.5
    for p in paras(): note("tab at start", (p.getString(), p.NumberingLevel, p.ListLabelString))
    fresh(); yield 0.4
    T("a) item"); K("Return"); yield 0.6
    for p in paras(): note("a)", (p.getString(), p.NumberingIsNumber, p.ListLabelString))
    fresh(); yield 0.4
    T("A. item"); K("Return"); yield 0.6
    for p in paras(): note("A.", (p.getString(), p.NumberingIsNumber, p.ListLabelString))
    fresh(); yield 0.4
    T("i. item"); K("Return"); yield 0.6
    for p in paras(): note("i.", (p.getString(), p.NumberingIsNumber, p.ListLabelString))
    fresh(); yield 0.4
    T("- dash"); K("Return"); yield 0.6
    for p in paras(): note("- ", (p.getString(), p.NumberingIsNumber, p.ListLabelString))
    fresh(); yield 0.4
    T("> arrow"); K("Return"); yield 0.6
    for p in paras(): note("> ", (p.getString(), p.NumberingIsNumber, p.ListLabelString))
def rules():
    for s in ("---", "===", "***", "___", "~~~", "###"):
        fresh(); yield 0.4
        T("before"); K("Return"); T(s); K("Return"); yield 0.8
        note(s, [(p.getString(), p.BottomBorder.OuterLineWidth + p.BottomBorder.LineWidth) for p in paras()])
    shot("w1c_rule")
def case():
    fresh(); yield 0.4
    T("hello world"); K("ctrl+shift+Left"); yield 0.3
    for i in range(3):
        K("shift+F3"); yield 0.5; note("shift+F3 #%d" % i, repr(text()))
run_scenarios(nav, copyfmt, lists, rules, case)
