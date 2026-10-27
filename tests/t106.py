exec(open("/home/claude/folio2/tests/common.py").read())
from folio import contentcontrols as CC, docapi
A = win.actions; m = lambda: win.engine.model
win.dialogs.message = lambda *a, **k: log("MSG", a)
def s0(): CC.insert(win, "dropdown")
def s1(): docapi.view_cursor(m()).gotoEnd(False); CC.insert(win, "date")
def s2(): docapi.view_cursor(m()).gotoEnd(False); CC.insert(win, "combo")
def s3(): docapi.view_cursor(m()).gotoEnd(False); CC.insert(win, "picture")
def s4(): app.quit()
steps(s0, s1, s2, s3, s4, delay=1500)
