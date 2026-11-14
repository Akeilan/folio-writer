import os as _o; TESTS = _o.environ["FOLIO_WRITER_TESTS"]; exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read()); exec(open("/tmp/p5/probes/ph.py").read()); exec(open("/tmp/p5/probes/rtlib.py").read())
def a():
    yield 1.0
    focus(); fresh(); yield 0.3
    build(); yield 1.0
    inv = inventory()
    json.dump(inv, open("/tmp/p5out/crash_inv.json", "w"))
    note("autorecover setting", (win.app.settings.get("autorecover", True), win.app.settings.get("autorecover_minutes", 10)))
    win.app.write_autorecover(win); yield 0.5
    note("autorecover files", os.listdir(win.app.autorecover_dir))
    log("ALLDONE-crash")
    os._exit(9)       # the crash
run_scenarios(a)
