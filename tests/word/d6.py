import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
exec(open(TESTS + "/word/w14.py").read().split("def smartcut")[0].split("exec(open")[-1].split("\n",1)[1] if False else "")
def a():
    fresh(); yield 0.3
    T("one two three"); yield 0.4
    find("two").select(); yield 0.4
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
