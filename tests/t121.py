exec(open("/home/claude/folio2/tests/common.py").read())
from folio import docapi, eqnumber
e = win.engine; m = lambda: e.model
st={}
V = open("/tmp/variant").read().strip()
def s0(): st["o"] = docapi.insert_formula(m(), "a+b", display=True)
def s1():
    o=st["o"]; a=o.getAnchor(); t=a.getText()
    after = t.createTextCursorByRange(a.getEnd())
    if "1" in V: after.gotoEndOfParagraph(True)
    before = t.createTextCursorByRange(a.getStart())
    if "2" in V: before.gotoStartOfParagraph(True)
    after.setString("\t(1)")
    if "3" in V: before.getString()
    before.setString("\t")
    log("applied", V)
def s2(): docapi.set_formula(st["o"], "a+b+c"); log("set")
steps(s0, s1, s2, lambda: app.quit(), delay=1500)
