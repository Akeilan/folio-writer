exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
def d():
    fresh(); yield 0.5
    T("Intro line"); K("Return"); yield 0.3
    T("- dash item"); yield 0.6
    note("before enter", para_texts())
    K("Return"); yield 0.8
    note("after enter", [(p.getString(), p.NumberingIsNumber, p.ListLabelString) for p in paras()])
    T("next item"); yield 0.6
    note("after typing", [(p.getString(), p.NumberingIsNumber, p.ListLabelString) for p in paras()])
    shot("w1d_dash")
run_scenarios(d)
