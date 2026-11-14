import os as _o; TESTS = _o.environ["FOLIO_WRITER_TESTS"]; exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read()); exec(open("/tmp/p5/probes/ph.py").read())
def a():
    yield 0.5
    focus()
    for src in ("Wait... what?", "Well ... fine", "He said... ", "so... what then", "A... b", "\"Well...\" she said", "said--\"Go!\"", "one--two three", "He ran -- fast ", "ok. ... ok"):
        fresh(); yield 0.15
        T("Lead in text. " + src + " "); yield 0.25
        note("typed %r" % src, repr(text().rstrip()))
    fresh(); T("teh "); yield 0.3; K("ctrl+z"); yield 0.3; t1 = text(); K("ctrl+z"); yield 0.3
    note("undo x1, x2 after 'teh ' at paragraph start", (t1, text()))
run_scenarios(a)
