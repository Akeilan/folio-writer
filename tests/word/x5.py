import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
def d():
    fresh(); yield 0.3
    T("Head"); K("ctrl+alt+1"); yield 0.3
    K("alt+shift+Right"); yield 0.6
    check("demote quick", style_of(0) == "Heading 2", style_of(0))
    K("alt+shift+Left"); yield 0.6
    check("promote", style_of(0) == "Heading 1", style_of(0))
    fresh(); yield 0.3
    T("hello"); K("shift+F10"); yield 1.0
    shot("x5_sf10")
    note("popups", len(popups()))
    K("Escape")
run_scenarios(d)
