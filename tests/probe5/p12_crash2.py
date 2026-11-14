import os as _o; TESTS = _o.environ["FOLIO_WRITER_TESTS"]; exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read()); exec(open("/tmp/p5/probes/ph.py").read()); exec(open("/tmp/p5/probes/rtlib.py").read())
def a():
    global win, E
    yield 0.5
    d = dialogs_open()
    note("dialogs at start", [x.get_title() for x in d])
    shot("recovery_prompt")
    check("Page offers to recover after a crash", any("Recover" in (x.get_title() or "") for x in d), [x.get_title() for x in d])
    for x in d:
        for r in (Gtk.ResponseType.YES, Gtk.ResponseType.OK, Gtk.ResponseType.ACCEPT):
            if x.get_widget_for_response(r) is not None:
                x.response(r); break
    yield 3.0
    wins = win.app.windows
    note("windows", [w.doc_name() for w in wins])
    win = wins[-1]; E = win.engine
    yield 1.0
    base = json.load(open("/tmp/p5out/crash_inv.json"))
    got = inventory()
    dd = diff(base, got)
    note("lost in recovery", " ;; ".join(dd))
    check("the recovered document has everything the crashed one had", not dd, "%d differences" % len(dd))
    shot("recovered")
run_scenarios(a)
