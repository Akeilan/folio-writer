exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
def tc():
    fresh(); yield 0.3
    win.actions.insert_text("Alpha bravo charlie. Delta echo foxtrot golf hotel.")
    E.command(".uno:InsertPara"); win.actions.insert_text("Second paragraph.")
    yield 0.8
    r = find("echo"); r.caret_to_start(); yield 0.3
    x0, y0, w, h = win._follow_rect
    xy = doc_screen(x0 + 100, y0 + h / 2)
    for d in (60, 120, 200):
        click(xy[0], xy[1]); yield 0.8
        X("mousemove", *xy); X("click", "--repeat", 3, "--delay", d, 1); yield 0.9
        note("triple delay %d" % d, repr(sel()))
    click(xy[0], xy[1]); yield 0.8
    X("click", "--repeat", 4, "--delay", 100, 1); yield 0.9
    note("quadruple", repr(sel()))
run_scenarios(tc)
