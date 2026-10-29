import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
def ed():
    return E.ed
def a():
    yield 1.0
    check("native engine", getattr(E, "native", False), type(E).__name__)
    focus(); yield 0.3
    T("Hello world. This is the new engine typing away."); yield 0.5
    s = ed().state()
    note("state", s)
    check("typed", ed().selected_text() == "" and ed().counts()[0] == 9, ed().counts())
    K("ctrl+a"); yield 0.2
    K("ctrl+b"); yield 0.4
    check("bold all", ed().state()["bold"], ed().state())
    K("End"); yield 0.2
    T("\nSecond line"); yield 0.5
    check("two paras", ed().counts()[0] == 11, ed().counts())
    K("ctrl+z"); yield 0.3
    note("after undo", ed().counts())
    win.run(("style", "Heading 1")); yield 0.4
    check("heading", ed().state()["style"] == "Heading 1", ed().state()["style"])
    shot("n1"); yield 0.3
    ok = win.save_to("/tmp/n1.docx"); yield 1.0
    check("saved", ok and os.path.exists("/tmp/n1.docx"))
    win.engine.ed.mark_saved()
run_scenarios(a)
