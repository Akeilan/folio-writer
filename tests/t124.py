import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
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
