import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
from folio import contentcontrols as CC, docapi
A = win.actions; m = lambda: win.engine.model
win.dialogs.message = lambda *a, **k: log("MSG", a)
def s0(): CC.insert(win, "dropdown")
def s1(): docapi.view_cursor(m()).gotoEnd(False); CC.insert(win, "date")
def s2(): docapi.view_cursor(m()).gotoEnd(False); CC.insert(win, "combo")
def s3(): docapi.view_cursor(m()).gotoEnd(False); CC.insert(win, "picture")
def s4(): app.quit()
steps(s0, s1, s2, s3, s4, delay=1500)
