exec(open("/home/claude/folio2/tests/common.py").read())
import os
from folio import review as RV
e = win.engine; A = win.actions
D = "/tmp/t148"; os.makedirs(D, exist_ok=True)
st = {}
def s0():
    A.insert_text("The quick brown fox jumps.")
    e.save_as(D + "/orig.odt")
def s1():
    e.command(".uno:SelectAll"); A.insert_text("The slow brown fox leaps.")
    e.save_as(D + "/rev.odt")
def s2():
    w = app.new_window(template=D + "/rev.odt")
    w.compare_sources = {"original": D + "/orig.odt", "revised": D + "/rev.odt"}
    w.source_windows = {}
    st["w"] = w
def s3a():
    log("pre", st["w"].engine.model.Text.getString())
def s3():
    w = st["w"]
    from folio.engine import file_url
    w.engine.command(".uno:CompareDocuments", {"URL": file_url(D + "/orig.odt"), "NoAcceptDialog": True})
def s4():
    w = st["w"]
    rl = w.engine.model.getRedlines()
    en = rl.createEnumeration(); n = 0
    while en.hasMoreElements(): en.nextElement(); n += 1
    log("changes", n, w.engine.model.Text.getString())
    w.engine.model.RecordChanges = True
    RV.show_sources(w, "both")
def s5():
    w = st["w"]
    log("sources", sorted(w.source_windows), RV.source_state(w))
    log("ro", [x.read_only for x in w.source_windows.values()])
    shot("t148a")
def s6():
    w = st["w"]
    RV.show_sources(w, "original")
    w.actions.cmd(".uno:AcceptAllTrackedChanges"); w.stop_tracking()
def s7():
    w = st["w"]
    log("after", sorted(w.source_windows), w.engine.model.RecordChanges,
        w.engine.model.getRedlines().createEnumeration().hasMoreElements(),
        w.engine.model.Text.getString())
    app.quit()
steps(s0, s1, s2, s3a, s3, s4, s5, s6, s7, delay=2500)
