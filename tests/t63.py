exec(open("/home/claude/folio2/tests/common.py").read())
A = win.actions
def s0(): A.insert_text("Original sentence here. Another line follows. ")
def s1(): A.cmd(".uno:TrackChanges"); A.insert_text("Added words. ")
def s2(): A.cmd(".uno:GoToStartOfDoc"); A.cmd(".uno:WordRightSel"); A.cmd(".uno:Delete")
def s3():
    log(str(win.engine.view.get_command_values(".uno:AcceptTrackedChanges"))[:900]); log(str(win.engine.view.get_command_values(".uno:ViewTrackChanges"))[:200])
    log("state margin", win.engine.state.get(".uno:ShowChangesInMargin"))
    app.quit()
steps(s0, s1, s2, s3, delay=2000)
