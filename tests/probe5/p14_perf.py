import os as _o; TESTS = _o.environ["FOLIO_WRITER_TESTS"]; exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read()); exec(open("/tmp/p5/probes/ph.py").read())
LOADED = {"n": 0}
_l = win._loaded
def _loaded(ok):
    LOADED["n"] += 1
    return _l(ok)
win._loaded = _loaded
V = win.engine.view
def idle():
    while Gtk.events_pending():
        Gtk.main_iteration_do(False)
def timed(fn):
    idle(); t0 = time.time(); fn(); idle(); return time.time() - t0
def a():
    yield 0.5
    for f in ("/tmp/corpus/novel.docx", "/tmp/p5out/files/big.txt"):
        n0 = LOADED["n"]; t0 = time.time()
        win.open_file(f)
        while LOADED["n"] == n0 and time.time() - t0 < 180:
            yield 0.05
        t_open = time.time() - t0
        yield 1.0
        e = ed(); pages = e.page_count()
        note("OPEN " + os.path.basename(f), "%.1fs, %d pages, %s words" % (t_open, pages, e.counts()[0]))
        focus()
        res = {}
        e.move_caret("doc_start", False)
        res["type at start (per key)"] = sum(timed(lambda: (K("x"),)) for _ in range(5)) / 5 - 0.18
        res["engine type at start"] = timed(lambda: (e.type_text("y"), V.after_edit()))
        res["ctrl+End"] = timed(lambda: K("ctrl+End")) - 0.18
        res["engine type at end"] = timed(lambda: (e.type_text("z"), V.after_edit()))
        res["type at end (per key)"] = sum(timed(lambda: (K("x"),)) for _ in range(5)) / 5 - 0.18
        res["Enter at end"] = timed(lambda: K("Return")) - 0.18
        res["ctrl+Home"] = timed(lambda: K("ctrl+Home")) - 0.18
        res["Enter at start"] = timed(lambda: K("Return")) - 0.18
        res["PageDown x10"] = timed(lambda: [K("Next") for _ in range(10)]) - 1.8
        res["select all + bold"] = timed(lambda: (K("ctrl+a"), K("ctrl+b"))) - 0.36
        res["undo that"] = timed(lambda: K("ctrl+z")) - 0.18
        res["find all 'dolor'"] = timed(lambda: e.find_all("dolor", None))
        res["save docx"] = timed(lambda: e.save("/tmp/p5out/perf.docx"))
        res["autorecover (odt)"] = timed(lambda: win.engine.save_as("/tmp/p5out/perf.odt", "odt", keep=False))
        res["export pdf"] = timed(lambda: win.engine.save_as("/tmp/p5out/perf.pdf", keep=False))
        res["zoom to 50%"] = timed(lambda: V.set_zoom(0.5)); V.set_zoom(1.0)
        for k, v in res.items():
            note("  " + k, "%.2fs" % max(0.0, v))
        mem = int(open("/proc/self/status").read().split("VmRSS:")[1].split()[0]) // 1024
        note("  memory", "%d MB" % mem)
        e.mark_saved()
run_scenarios(a)
