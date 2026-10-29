import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
def where():
    return repr(pos())
def nav():
    fresh(); yield 0.4
    T("one two three"); K("Return"); T("second para"); K("Return"); T("third"); yield 0.8
    note("paras", para_texts())
    K("Home"); yield 0.3; note("Home", where())
    K("End"); yield 0.3; note("End", where())
    K("ctrl+Home"); yield 0.3; note("ctrl+Home", where())
    K("ctrl+Down"); yield 0.3; note("ctrl+Down", where() + caret_para_text())
    K("End"); yield 0.3; note("End2", where())
    K("shift+Home"); yield 0.3; note("shift+Home", repr(sel()))
    K("ctrl+Up"); yield 0.3; note("ctrl+Up", where())
    K("Home"); K("ctrl+Delete"); yield 0.5; note("ctrl+Delete", para_texts())
def copyfmt():
    fresh(); yield 0.4
    T("fmt"); yield 0.3
    K("ctrl+shift+Left"); yield 0.3; note("sel", repr(sel()))
    K("ctrl+b"); yield 0.3; note("text", repr(text()))
    K("ctrl+shift+c"); yield 0.5; note("after ctrl+shift+c", repr(text()))
def lists():
    fresh(); yield 0.4
    T("1. first"); K("Return"); T("second"); yield 0.5
    K("Home"); yield 0.3; K("Tab"); yield 0.5
    for i, t in enumerate(para_texts()): note("tab at start", (t, list_level(i), list_label(i)))
    fresh(); yield 0.4
    T("a) item"); K("Return"); yield 0.6
    for i, t in enumerate(para_texts()): note("a)", (t, is_listed(i), list_label(i)))
    fresh(); yield 0.4
    T("A. item"); K("Return"); yield 0.6
    for i, t in enumerate(para_texts()): note("A.", (t, is_listed(i), list_label(i)))
    fresh(); yield 0.4
    T("i. item"); K("Return"); yield 0.6
    for i, t in enumerate(para_texts()): note("i.", (t, is_listed(i), list_label(i)))
    fresh(); yield 0.4
    T("- dash"); K("Return"); yield 0.6
    for i, t in enumerate(para_texts()): note("- ", (t, is_listed(i), list_label(i)))
    fresh(); yield 0.4
    T("> arrow"); K("Return"); yield 0.6
    for i, t in enumerate(para_texts()): note("> ", (t, is_listed(i), list_label(i)))
def rules():
    for s in ("---", "===", "***", "___", "~~~", "###"):
        fresh(); yield 0.4
        T("before"); K("Return"); T(s); K("Return"); yield 0.8
        note(s, [(t, border("bottom", i)) for i, t in enumerate(para_texts())])
    shot("w1c_rule")
def case():
    fresh(); yield 0.4
    T("hello world"); K("ctrl+shift+Left"); yield 0.3
    for i in range(3):
        K("shift+F3"); yield 0.5; note("shift+F3 #%d" % i, repr(text()))
run_scenarios(nav, copyfmt, lists, rules, case)
