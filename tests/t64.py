exec(open("/home/claude/folio2/tests/common.py").read())
from folio import review, docapi
A = win.actions; st={}
def s0(): win.unmaximize(); win.resize(1590,960); win.move(0,0); A.insert_text("Original sentence here. Another line follows. ")
def s1(): A.cmd(".uno:TrackChanges"); A.insert_text("Added words. ")
def s2(): A.cmd(".uno:GoToStartOfDoc"); A.cmd(".uno:WordRightSel"); A.cmd(".uno:Delete")
def s3(): win.markup_choice.set_active(1)
def s4(): log("bars", win.change_bars.bars()); shot("simple"); win.markup_choice.set_active(0)
def s5(): shot("allmarkup"); win.set_balloons(True)
def s6(): shot("balloons"); win.set_balloons(False); A.cmd(".uno:TrackChanges")
def s7():
    # compare: save two versions
    A.cmd(".uno:AcceptAllTrackedChanges")
def s8(): win.save_to("/tmp/cmp_a.odt"); A.cmd(".uno:GoToEndOfDoc"); A.insert_text("Brand new ending.")
def s9(): win.save_to("/tmp/cmp_b.odt")
def s10():
    w = app.new_window(template="/tmp/cmp_b.odt"); st["w"] = w
def s11():
    from folio.engine import file_url
    st["w"].engine.command(".uno:CompareDocuments", {"URL": file_url("/tmp/cmp_a.odt"), "NoAcceptDialog": True})
def s12():
    raw = st["w"].engine.view.get_command_values(".uno:AcceptTrackedChanges"); log("compare redlines", raw[:300] if raw else raw)
    st["w"].present(); shot("compare")
def s13():
    m = win.engine.model; review.set_restriction(m, {"on": True, "mode": "readonly", "hash": ""}); review.enforce(win)
    A.insert_text("SHOULD NOT APPEAR")
def s14():
    log("restricted text", "SHOULD NOT" in win.engine.model.getText().getString()); app.quit()
steps(s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12, s13, s14, delay=2000)
