exec(open("/home/claude/folio2/tests/common.py").read())
e = win.engine
A = win.actions
from folio import docapi
def dump(tag):
    m = e.model
    en = m.getText().createEnumeration(); out = []
    while en.hasMoreElements():
        p = en.nextElement()
        try: out.append(p.getString()[:40] + ("[OBJ]" if "￼" in p.getString() else ""))
        except Exception: out.append("<table>")
    vc = docapi.view_cursor(m)
    log(tag, out, "vc:", repr(vc.getText().createTextCursorByRange(vc).getString()))
def s1(): A.insert_text("Revenue grew: ")
def s2(): dump("after text")
def s3(): win.eqbar.new_equation("R(t)=R_0 e^(kt)")
def s4(): dump("after eq")
def s5(): win.eqbar.finish()
def s6(): dump("after finish"); e.command(".uno:InsertPara")
def s7(): dump("after para"); A.insert_text("Next line")
def s8(): dump("end"); shot("t5"); app.quit()
steps(s1, s2, s3, s4, s5, s6, s7, s8, delay=1200)
