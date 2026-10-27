exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
exec(open("/home/claude/folio2/tests/word/w14.py").read().split("def smartcut")[0].split("exec(open")[-1].split("\n",1)[1] if False else "")
def a():
    fresh(); yield 0.3
    T("one two three"); yield 0.4
    docapi.controller(M()).select(find("two")); yield 0.4
    K("ctrl+x"); yield 0.6
    note("after cut", repr(text()))
    note("owned", win.clipboard_owned)
    note("clip", repr(getattr(win.actions, "_clip_data", None)))
    K("End"); yield 0.3
    note("before space", repr(text()))
    K("space"); yield 0.5
    note("after space", repr(text()))
    K("ctrl+v"); yield 0.8
    note("after paste", repr(text()))
run_scenarios(a)
