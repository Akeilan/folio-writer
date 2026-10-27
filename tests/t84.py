exec(open("/home/claude/folio2/tests/common.py").read())
from folio import docapi, statusbar
A = win.actions; m = lambda: win.engine.model
def s0(): A.insert_text("Line one text"); win.engine.command(".uno:InsertPara"); A.insert_text("Second paragraph " + "word "*40); win.engine.command(".uno:InsertPara"); A.insert_text("Third")
def s1():
    vc = docapi.view_cursor(m()); p1 = vc.getPosition(); vc.gotoStart(False); p0 = vc.getPosition(); vc.gotoEnd(False)
    log("pos", p0.X, p0.Y, p1.X, p1.Y)
    r = statusbar.cursor_metrics(m(), True)
    log(r, docapi.view_cursor(m()).getPosition().Y)
def s2(): app.quit()
steps(s0, s1, s2, delay=1500)
