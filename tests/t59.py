exec(open("/home/claude/folio2/tests/common.py").read())
from folio import mailings as M
A = win.actions; m = lambda: win.engine.model; st={}
def s0():
    win.unmaximize(); win.resize(1590,960); win.move(0,0)
    cols, rows = M.read_csv("/tmp/people.csv"); M.set_recipients(m(), cols, rows, "/tmp/people.csv"); M.set_merge_type(m(), "letters"); win.refresh_mailings()
def s1(): M.insert_address_block(m())
def s2(): A.cmd(".uno:InsertPara"); A.cmd(".uno:InsertPara")
def s2b(): M.insert_greeting(m(), "Dear", ",")
def s2c(): A.cmd(".uno:InsertPara"); A.insert_text("Thanks for your order.")
def s3(): log("template", repr(m().getText().getString())); win.select_tab("Mailings"); shot("mail0"); win.run("merge-preview")
def s4(): log("preview", repr(m().getText().getString())); win.merge_go("next")
def s5(): log("rec2", repr(m().getText().getString()[:40])); shot("mail1"); win.run("merge-preview")
def s6():
    path = M.merge(m(), "all"); log("merged path", path)
    st["w"] = app.new_window(template=path)
def s7(): log("merged", repr(st["w"].engine.model.getText().getString()), "fields left", st["w"].engine.model.getTextFields().createEnumeration().hasMoreElements())
def s8():
    from folio import dlg_mail
    import folio.mailings as MM
    MM.highlight_fields(True); shot("mail_hl"); MM.highlight_fields(False); app.quit()
steps(s0, s1, s2, s2b, s2c, s3, s4, s5, s6, s7, s8, delay=2500)
