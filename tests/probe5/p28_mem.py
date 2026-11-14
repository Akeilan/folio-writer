import os as _o; TESTS = _o.environ["FOLIO_WRITER_TESTS"]; exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
def rss(): return int(open("/proc/self/status").read().split("VmRSS:")[1].split()[0]) // 1024
def a():
    yield 1.0
    note("start", rss())
    win.open_file("/tmp/corpus/long.docx"); yield 3.0
    note("92 pages open", rss())
    win.open_file("/tmp/corpus/novel.docx"); yield 4.0
    note("490 pages open", rss())
    V = win.engine.view
    for i in range(0, 490, 25):
        win.engine.ed.goto_page(i); V.after_move(); yield 0.15
    note("after scrolling through it", rss())
    win.open_file("/tmp/corpus/oneline.docx"); yield 3.0
    note("back to a one-line document", rss())
    for k in range(3):
        win.open_file("/tmp/corpus/novel.docx"); yield 3.0
        win.open_file("/tmp/corpus/oneline.docx"); yield 2.0
    note("after opening the novel three more times", rss())
    ok = win.engine.save_as("/tmp/p5out/x.epub", keep=False); yield 1.0
    note("epub export", (ok, os.path.exists("/tmp/p5out/x.epub"), getattr(win.engine, "save_error", None)))
run_scenarios(a)
