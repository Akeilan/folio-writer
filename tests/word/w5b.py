exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
def word_xy(word, frac):
    c = vc(); r = find(word); c.gotoRange(r.getStart(), False); yield 0.3
    x0, y0, w, h = win._follow_rect
    c.gotoRange(r.getEnd(), False); yield 0.3
    x1 = win._follow_rect[0]
    P["xy"] = doc_screen(x0 + (x1 - x0) * frac, y0 + h / 2)
P = {}
def painter():
    fresh(); yield 0.3
    T("source target"); yield 0.4
    yield from word_xy("source", 0.5); click(*P["xy"], n=2); yield 0.5
    K("ctrl+b"); yield 0.4
    note("source weight", find("source").CharWeight)
    fp = find_control("Home", "Format Painter")
    note("fp", type(fp).__name__)
    w = fp
    click(*widget_center(w)); yield 0.6
    yield from word_xy("target", 0.05); a = P["xy"]
    yield from word_xy("target", 0.95); b = P["xy"]
    X("mousemove", *a); X("mousedown", 1)
    for i in range(1, 8): X("mousemove", int(a[0] + (b[0] - a[0]) * i / 7), a[1]); time.sleep(0.05)
    X("mouseup", 1); yield 1.2
    note("target weight after painter drag", find("target").CharWeight)
    shot("w5b_painter")
    # painter by single click on a word
    T(" more"); yield 0.3
    yield from word_xy("source", 0.5); click(*P["xy"], n=2); yield 0.4
    click(*widget_center(w)); yield 0.6
    yield from word_xy("more", 0.5); click(*P["xy"]); yield 1.0
    note("more weight after painter click", find("more").CharWeight)
run_scenarios(painter)
