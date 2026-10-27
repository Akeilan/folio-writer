exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
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
