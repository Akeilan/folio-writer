exec(open("/home/claude/folio2/tests/common.py").read())
from folio.keys import BINDINGS
e = win.engine
cmds = []
for spec, act in BINDINGS:
    if isinstance(act, str) and act.startswith(".uno:"):
        cmds.append(act)
    elif isinstance(act, tuple) and isinstance(act[0], str) and act[0].startswith(".uno:"):
        cmds.append(act[0])
for c in win.ribbon.controls:
    a = getattr(c, "action", None)
    if isinstance(a, str) and a.startswith(".uno:"):
        cmds.append(a)
skip = {".uno:InsertText"}
cmds = [c for c in dict.fromkeys(cmds) if c not in skip]
log("testing", len(cmds))
current = [None]
def onwin(v, payload):
    log("WINDOW EVENT during", current[0], payload[:160])
try:
    e.view.connect("window", onwin)
except TypeError as ex:
    log("no window signal", ex)
def prep():
    e.command(".uno:InsertText", {"Text": "Some words here for testing. Another sentence follows."})
    e.command(".uno:SelectWord")
fns = [prep]
for c in cmds:
    def f(c=c):
        current[0] = c
        e.command(c)
    f.__name__ = c
    fns.append(f)
    def undo(c=c):
        e.command(".uno:Escape")
    fns.append(undo)
fns.append(lambda: (log("done"), app.quit()))
steps(*fns, delay=250)
