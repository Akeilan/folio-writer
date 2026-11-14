import os as _o; TESTS = _o.environ["FOLIO_WRITER_TESTS"]; exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read()); exec(open("/tmp/p5/probes/ph.py").read()); exec(open("/tmp/p5/probes/rtlib.py").read())
def a():
    yield 1.0
    focus(); fresh(); yield 0.3
    build(); yield 1.0
    K("ctrl+Home"); yield 0.5
    shot("v_doc_top")
    V = win.engine.view
    V.set_zoom(0.6); yield 0.6; shot("v_doc_60"); V.set_zoom(1.0); yield 0.3
    for t in win.ribbon.tabs:
        nm = getattr(t, "name", None)
        if nm in ("Insert", "Design", "Layout", "References", "Mailings", "Review", "View", "Draw", "Developer", "Help"):
            win.ribbon.show_tab(nm) if hasattr(win.ribbon, "show_tab") else None
            yield 0.5; shot("v_tab_" + nm.replace(" ", ""))
    note("ribbon api", [n for n in dir(win.ribbon) if not n.startswith("_")][:60])
run_scenarios(a)
