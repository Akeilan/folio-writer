import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
def word_xy(word, frac, nth=0):
    r = find(word, nth); r.caret_to_start(); yield 0.3
    x0, y0, w, h = win._follow_rect
    r.caret_to_end(); yield 0.3
    x1 = win._follow_rect[0]
    P["xy"] = doc_screen(x0 + (x1 - x0) * frac, y0 + h / 2)
P = {}
def d():
    fresh(); yield 0.3
    T("one two three"); K("ctrl+Left"); K("ctrl+shift+Left"); yield 0.5
    note("sel", repr(sel()))
    K("ctrl+x"); yield 0.8
    note("smart cut", repr(text()))
    K("End"); T(" "); K("ctrl+v"); yield 0.8
    note("smart paste", repr(text()))
run_scenarios(d)
