import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
exec(open(TESTS + "/word/w14.py").read().split("def ac_undo")[0].split("\n",2)[2])
def a():
    fresh(); yield 0.3
    T("src a b c"); yield 0.6
    note("text", repr(text()))
    find("src").select(); yield 0.3
    K("ctrl+b"); yield 0.5
    note("src bold", find("src").run()["bold"])
    win.engine.command(".uno:FormatPaintbrush"); yield 0.5
    note("painter state", win.engine.get(".uno:FormatPaintbrush"))
    yield from word_xy(" a", 0.8)
    note("painter state2", win.engine.get(".uno:FormatPaintbrush"))
    note("xy", P["xy"])
    K("ctrl+End"); yield 0.3
    click(*P["xy"]); yield 0.8
    note("left of cursor", repr(pos()))
    note("a weight", find(" a").run()["bold"])
run_scenarios(a)
