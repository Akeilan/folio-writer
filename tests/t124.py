exec(open("/home/claude/folio2/tests/common.py").read())
from folio import imagecharts as IC
e = win.engine; m = lambda: e.model
st={}
def s0(): st["a"] = IC.insert(m(), "treemap"); e.command(".uno:InsertPara")
def s1():
    e.command(".uno:GoToEndOfDoc"); st["b"] = IC.insert(m(), "sunburst")
def s2():
    IC.set_option(m(), st["b"], legend="right", values=True, style=5)
    log("graphic", st["a"].Graphic.MimeType if hasattr(st["a"].Graphic, "MimeType") else st["a"].Graphic)
def s3(): shot("t124"); app.quit()
steps(s0, s1, s2, s3, delay=2000)
