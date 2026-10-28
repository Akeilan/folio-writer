exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
def d():
    fresh(); yield 0.3
    win.actions.cmd(".uno:InsertTable", {"Columns": 3, "Rows": 3}); yield 1.0
    win.select_tab("Table Design"); yield 1.0
    shot("w13_tdesign")
    fresh(); yield 0.3
    insert_picture("/tmp/wfid/pic.png"); yield 1.2
    check("picture inserted", len(objects("Picture")) == 1, objects())
    win.update_object_tabs(); yield 0.5
    win.select_tab("Picture Format"); yield 1.0
    shot("w13_pformat")
    fresh(); yield 0.3
    rib("Insert", "Shapes", "Rectangle"); yield 0.5
    win.draw.cancel() if win.draw.active else None
    win.select_tab("Header & Footer") if False else None
run_scenarios(d)
