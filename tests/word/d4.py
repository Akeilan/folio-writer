exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
def a():
    fresh(); yield 0.3
    T("Base text."); yield 0.4
    win.actions.cmd(".uno:TrackChanges"); yield 0.4
    K("End"); T(" Added by me."); yield 0.8
    um = M().getUndoManager()
    note("titles0", um.getAllUndoActionTitles()[:5])
    win.engine.command(".uno:RejectAllTrackedChanges"); yield 1.0
    note("after reject", (text(), um.getAllUndoActionTitles()[:5]))
    win.engine.command(".uno:Undo"); yield 1.0
    note("after undo", (text(), um.getAllUndoActionTitles()[:5]))
run_scenarios(a)
