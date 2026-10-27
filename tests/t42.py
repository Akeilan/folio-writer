exec(open("/home/claude/folio2/tests/common.py").read())
A = win.actions
def s0():
    win.unmaximize(); win.resize(1590, 960); win.move(0,0)
    A.insert_text("Above table."); A.cmd(".uno:InsertPara")
def s0b(): win.dialogs._new_table(5, 4)
def s1():
    for i in range(20):
        A.insert_text("Cell%d" % i); A.cmd(".uno:JumpToNextCell") if False else A.cmd(".uno:GoRight")
def s2(): shot("tdesign_new"); A.cmd(".uno:GoToStartOfDoc"); A.cmd(".uno:GoDown")
def s3():
    t = win.ribbon
    t.select([x for x in t.tabs if x.name=="Table Design"][0])
def s4(): shot("tdesign0"); win.run(("table-style2", ("grid4", 0x4472C4)))
def s5(): shot("tdesign1"); win.table_opt_checks["banded_rows"].set_active(False)
def s6(): shot("tdesign2"); win.table_opt_checks["first_col"].set_active(False); win.run(("table-style2", ("list3", 0xED7D31)))
def s7(): shot("tdesign3"); win.table_style_gallery.more(win.table_style_gallery)
def s8(): shot("tdesign4"); win.table_style_gallery.get_toplevel(); [w.popdown() for w in []]; A.do_undo()
def s9(): A.do_undo(); A.do_undo(); A.do_undo()
def s10(): log("after undos", repr(win.engine.model.getText().getString()[:60]), win.engine.model.getTextTables().getCount()); app.quit()
steps(s0, s0b, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, delay=2000)
