import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
import subprocess
from folio import backstage as B
cap = {}
class R: returncode = 0; stderr = ""
def fake(args, **k): cap["a"] = args; return R()
def s0():
    win.actions.insert_text("Print me")
    win.show_backstage("print")
def s1():
    pass
def s2():
    shot("t150a")
    real = B.subprocess.run; B.subprocess.run = fake
    win.backstage._print("lp0", 1, "all", "", "one-sided", True, 4, "A4")
    log("args", cap.get("a"))
    app.quit()
steps(s0, s1, s2, delay=2000)
