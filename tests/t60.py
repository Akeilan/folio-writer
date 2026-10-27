exec(open("/home/claude/folio2/tests/common.py").read())
from folio import mailings as M, docapi
A = win.actions; m = lambda: win.engine.model; st={}
def s0(): win.unmaximize(); win.resize(1590,960); win.move(0,0); A.insert_text("Letter body.")
def s1(): M.envelope(m(), "Ann Jones\n1 Main St\nSpringfield, IL 62701", "Ron S.\n5 Home Rd\nTown, ST 11111", 0)
def s2(): log("env text", repr(m().getText().getString())); win.engine.command(".uno:GoToStartOfDoc"); shot("envelope")
def s3(): st["w"] = app.new_window()
def s4(): M.labels_document(st["w"].engine.model, "Ann Jones\n1 Main St\nSpringfield, IL", 0, True)
def s5(): log("label cells", st["w"].engine.model.getTextTables().getByIndex(0).getCellNames()[:3], len(st["w"].engine.model.getTextTables().getByIndex(0).getCellNames())); shot("labels"); app.quit()
steps(s0, s1, s2, s3, s4, s5, delay=2500)
