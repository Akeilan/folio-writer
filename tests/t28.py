import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
from folio import docapi
m = lambda: win.engine.model
def s0(): win.actions.insert_text("Date: "); win.actions.cmd(".uno:InsertDateField")
def s1():
    vs = m().getCurrentController().getViewSettings()
    names = [p.Name for p in vs.getPropertySetInfo().getProperties()]
    log([n for n in names if "ield" in n or "ommand" in n])
    try:
        vs.ShowFieldCommands = True; log("set ok")
    except Exception as e: log("err", e)
def s2(): shot("fieldcodes"); app.quit()
steps(s0, s1, s2, delay=1500)
