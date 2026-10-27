exec(open("/home/claude/folio2/tests/common.py").read())
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
