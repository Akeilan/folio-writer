exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
exec(open("/home/claude/folio2/tests/word/w14.py").read().split("def ac_undo")[0].split("\n",2)[2])
def a():
    fresh(); yield 0.3
    T("src a b c"); yield 0.6
    note("text", repr(text()))
    docapi.controller(M()).select(find("src")); yield 0.3
    K("ctrl+b"); yield 0.5
    note("src bold", find("src").CharWeight)
    win.engine.command(".uno:FormatPaintbrush"); yield 0.5
    note("painter state", win.engine.get(".uno:FormatPaintbrush"))
    yield from word_xy(" a", 0.8)
    note("painter state2", win.engine.get(".uno:FormatPaintbrush"))
    note("xy", P["xy"])
    K("ctrl+End"); yield 0.3
    click(*P["xy"]); yield 0.8
    c = vc(); note("cursor after click", repr(c.getText().createTextCursorByRange(c.getStart()).getString()))
    cc = vc().getText().createTextCursorByRange(vc().getStart()); cc.gotoStartOfParagraph(True); note("left of cursor", repr(cc.getString()))
    note("a weight", find(" a").CharWeight)
run_scenarios(a)
