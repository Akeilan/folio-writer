import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
def foc():
    w = win.get_focus()
    return (type(w).__name__, win.is_active(), [t.get_title() for t in Gtk.Window.list_toplevels() if t.get_visible()])
def a():
    fresh(); yield 0.3
    T("one"); yield 0.5; note("typed1", (repr(text()), foc()))
    K("ctrl+alt+1"); K("Return"); yield 0.3
    rib("References", "Table of Contents", "Automatic Table 1"); yield 1.5
    note("after toc", foc())
    T("two"); yield 0.5; note("typed2", repr(text()))
    rib("References", "Update Table"); yield 1.5
    note("after update", foc())
    T("three"); yield 0.5; note("typed3", repr(text()))
    fresh(); yield 0.4
    note("after fresh", foc())
    T("four"); yield 0.5; note("typed4", repr(text()))
run_scenarios(a)
