exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
def lists():
    for inp, label in (("a) ", "a)"), ("A. ", "A."), ("i. ", "i."), ("I. ", "I."), ("c) ", "c)"), ("(a) ", "(a)"), ("(1) ", "(1)")):
        fresh(); yield 0.4
        K("ctrl+shift+n"); yield 0.2
        T(inp + "item"); yield 0.8
        K("Return"); T("next"); yield 0.8
        p = paras()
        info = [(x.getString(), x.ListLabelString) for x in p]
        check("autolist %r" % inp, len(p) == 2 and p[0].getString() == "Item" or p[0].getString() == "item", info)
        check("autolist label %r" % inp, p[0].ListLabelString == label, info)
    fresh(); yield 0.4
    T("> arrow"); K("Return"); T("next"); yield 0.8
    p = paras()
    check("> starts arrow bullet", bool(p[0].NumberingIsNumber) and p[0].getString().lower() == "arrow", [(x.getString(), x.ListLabelString, x.NumberingIsNumber) for x in p])
    shot("r3_arrow")
    fresh(); yield 0.4
    T("Ann said a) was fine"); yield 0.6
    check("mid-sentence a) untouched", text() == "Ann said a) was fine", repr(text()))
def rule():
    fresh(); yield 0.4
    T("Before"); K("Return"); K("minus", "minus", "minus"); K("Return"); yield 0.8
    info = [(p.getString(), p.BottomBorder.OuterLineWidth) for p in paras()]
    check("--- Enter draws a line", info[0][1] > 0 and all(t == "" for t, _w in info[1:]), info)
    shot("r3_rule")
def comment():
    win.open_file("/tmp/wfid/fid.docx"); yield 5.0
    labs = [w.get_text() for w in find_widget(win, lambda w: isinstance(w, Gtk.Label) and w.get_text() == "Reviewer note")]
    check("imported comment shows its text", bool(labs), labs)
run_scenarios(lists, rule, comment)
