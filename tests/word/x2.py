exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
from folio import autolist
def d():
    real = autolist.on_return
    autolist.on_return = lambda w: False
    fresh(); yield 0.4
    T("Before"); K("Return"); yield 0.3
    K("minus", "minus", "minus"); yield 0.4; K("Return"); yield 0.8
    note("native", [(p.getString(), p.BottomBorder.OuterLineWidth) for p in paras()])
    autolist.on_return = real
    fresh(); yield 0.4
    T("Before"); K("Return"); yield 0.3
    K("minus", "minus", "minus"); yield 0.4; K("Return"); yield 0.8
    note("ours", [(p.getString(), p.BottomBorder.OuterLineWidth) for p in paras()])
run_scenarios(d)
