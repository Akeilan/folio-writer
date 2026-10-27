exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
def big():
    t0 = time.time()
    win.open_file("/tmp/wfid/big.docx")
    note("open_file returned after", round(time.time() - t0, 2))
    yield 15.0
    note("title", win.get_title())
    yield 2.0
    vc().jumpToLastPage(); note("pages", vc().getPage())
    vc().gotoStart(False); yield 1.0
    focus()
    # move to middle
    c = vc(); c.jumpToPage(60); yield 1.5
    n0 = len(text())
    t0 = time.time()
    T("typing speed test string with forty chars", delay=30)
    tt = time.time() - t0
    t1 = time.time()
    while len(text()) < n0 + 42 and time.time() - t1 < 20:
        yield 0.05
    note("type 42 chars: xdotool %.2fs, text complete after +%.2fs" % (tt, time.time() - t1), len(text()) - n0)
    t0 = time.time()
    for i in range(20): K("Next")
    yield 0.1
    note("20x PageDown seconds", round(time.time() - t0, 2))
    shot("w6_after_pgdn")
    t0 = time.time()
    K("ctrl+End"); yield 0.5
    note("ctrl+End page", vc().getPage())
    win.status.schedule_metrics() if hasattr(win.status, "schedule_metrics") else None
    t0 = time.time(); K("ctrl+a"); yield 0.3; K("ctrl+b"); 
    yield 0.2
    while find("Chapter 40").CharWeight < 150 and time.time() - t0 < 30:
        yield 0.2
    note("bold whole doc seconds", round(time.time() - t0, 2))
    K("ctrl+z"); yield 2
run_scenarios(big)
