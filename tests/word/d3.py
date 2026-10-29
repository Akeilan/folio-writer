import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
def a():
    fresh(); yield 0.3
    for i in range(3):
        win.actions.cmd(".uno:InsertPagebreak"); yield 0.2
    yield 1.0
    win.dialogs.zoom_pages(2); yield 2.0
    note("rects", win.engine.page_rects())
    shot("d3_many")
    win.dialogs.zoom_100(); yield 0.5
    win.engine.command(".uno:ViewLayout", {"Columns": ("short", 1), "BookMode": ("boolean", "false")}); yield 1.0
    note("rects after", win.engine.page_rects())
run_scenarios(a)
