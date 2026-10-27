exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
def word_xy(word, frac, nth=0):
    c = vc(); r = find(word, nth); c.gotoRange(r.getStart(), False); yield 0.3
    x0, y0, w, h = win._follow_rect
    c.gotoRange(r.getEnd(), False); yield 0.3
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
