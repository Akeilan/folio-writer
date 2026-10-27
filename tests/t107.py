exec(open("/home/claude/folio2/tests/common.py").read())
from folio import authorities as TOA, docapi
A = win.actions; m = lambda: win.engine.model
def s0():
    A.insert_text("As held in Smith v. Jones, 123 U.S. 456 (1990), the rule applies. See also 42 U.S.C. 1983. ")
    win.engine.command(".uno:InsertPagebreak"); A.insert_text("Again Smith v. Jones, 123 U.S. 456 (1990) matters.")
def s1():
    sd = m().createSearchDescriptor(); sd.SearchString = "Smith v. Jones, 123 U.S. 456 (1990)"
    f = m().findFirst(sd); log("n", TOA.mark(m(), f, f.getString(), "Smith", "Cases", True))
    sd.SearchString = "42 U.S.C. 1983"; f = m().findFirst(sd); TOA.mark(m(), f, f.getString(), "", "Statutes")
def s2(): docapi.view_cursor(m()).gotoEnd(False); win.engine.command(".uno:InsertPara"); TOA.insert_table(m())
def s3(): t = m().getText().getString(); log(repr(t[t.find("matters.")+8:])); shot("toa"); app.quit()
steps(s0, s1, s2, s3, delay=1800)
