import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
def big():
    t0 = time.time()
    win.open_file("/tmp/wfid/big.docx")
    note("open_file returned after", round(time.time() - t0, 2))
    yield 15.0
    note("title", win.get_title())
    yield 2.0
    note("pages", pages())
    caret_start(); yield 1.0
    focus()
    # move to middle
    E.ed.goto_page(59); E.view.after_move(); yield 1.5
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
    note("ctrl+End page", caret_page() + 1)
    win.status.schedule_metrics() if hasattr(win.status, "schedule_metrics") else None
    t0 = time.time(); K("ctrl+a"); yield 0.3; K("ctrl+b"); 
    yield 0.2
    while not find("Chapter 40").run()["bold"] and time.time() - t0 < 30:
        yield 0.2
    note("bold whole doc seconds", round(time.time() - t0, 2))
    K("ctrl+z"); yield 2
run_scenarios(big)
