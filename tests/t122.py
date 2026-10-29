import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
from folio import docapi
e = win.engine; m = lambda: e.model; ed = win.eqbar.ed
st = {}
def scr(x, y):
    ok, ox, oy = e.view.get_window().get_origin()
    return int(ox + x), int(oy + y)
def click(x, y):
    sx, sy = scr(x, y); subprocess.run(["xdotool", "mousemove", str(sx), str(sy), "click", "1"])
def s0():
    win.actions.insert_text("Text before."); e.command(".uno:InsertPara")
    win.eqbar.new_equation("a/b+c")
def s1():
    st["frame"] = ed.frame; log("frame", ed.frame)
    win.eqbar.finish()
    e.command(".uno:GoToStartOfDoc")
def s2():
    log("active after finish", ed.active)
    fx, fy, w, h = st["frame"]
    click(fx + 6, fy + h * 0.25)     # numerator area
def s3():
    log("after click: active", ed.active, "seq", [getattr(i,'value',type(i).__name__) for i in ed.caret[0].items], "idx", ed.caret[1])
    shot("t122a")
    fx, fy, w, h = ed.frame
    click(fx + w - 4, fy + h/2)      # near the end
def s4():
    log("click end: seq", [getattr(i,'value',type(i).__name__) for i in ed.caret[0].items], "idx", ed.caret[1])
    subprocess.run(["xdotool", "type", "z"])
def s5():
    log("lin", win.eqbar.entry.get_text())
    click(100, 60)   # outside
def s6():
    log("active after outside click", ed.active, [docapi.formula_of(o) for o in docapi.formulas(m())]); app.quit()
steps(s0, s1, s2, s3, s4, s5, s6, delay=1500)
