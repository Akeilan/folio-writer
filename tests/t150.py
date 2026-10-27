exec(open("/home/claude/folio2/tests/common.py").read())
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
