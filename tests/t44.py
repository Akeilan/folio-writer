exec(open("/home/claude/folio2/tests/common.py").read())
from folio import docapi
e = win.engine; A = win.actions; st = {}
def s0(): A.insert_text("Body."); A.cmd(".uno:InsertPara"); win.run("header")
def s1(): A.insert_text("Head text"); win.run("close-header-footer")
def s2(): A.cmd(".uno:GoToEndOfDoc"); win.dialogs._new_table(3, 3)
def s3(): A.insert_text("H1"); win.run(("table-style2", ("grid4", 0x70AD47)))
def s4(): log("saved", win.save_to("/tmp/rt2.docx")); log("ps", docapi.page_setup(e.model)["top"])
def s5(): st["w2"] = app.new_window("/tmp/rt2.docx")
def s6():
    m = st["w2"].engine.model; ps = docapi.page_style(m)
    log("header on", ps.HeaderIsOn, repr(ps.HeaderText.getString()), "top edge", ps.TopMargin, "body", docapi.page_setup(m)["top"])
    t = m.getTextTables().getByIndex(0); c = t.getCellByName("A1")
    log("A1 fill %06x" % (c.BackColor & 0xffffff), "B2 fill", c.BackColor, t.getCellByName("A2").BackColor)
    shot("rt2"); app.quit()
steps(s0, s1, s2, s3, s4, s5, s6, delay=2500)
