import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
import subprocess, time
from folio import docapi, drawing, arrange
m = lambda: win.engine.model
st = {}
def s0():
    win.unmaximize(); win.resize(1590,960); win.move(0,0); win.actions.insert_text("Arrange test")
    for i,(x,y) in enumerate(((3000,4000),(7000,6000),(12000,5000))):
        drawing.insert_shape(m(), "rectangle", 1, x, y, 2000, 1500)
def s1():
    objs = arrange.all_objects(m()); log("objs", [arrange.display_name(o,i) for i,o in enumerate(objs)])
    arrange.select(m(), objs); log("sel", len(arrange.selected_objects(m())))
    win.update_object_tabs()
    win.arrange_call("align", "top")
def s2():
    log("tops", [o.VertOrientPosition for o in arrange.all_objects(m())])
    arrange.select(m(), arrange.all_objects(m())); win.arrange_call("distribute", "h")
def s3():
    xs = sorted((o.HoriOrientPosition, o.Size.Width) for o in arrange.all_objects(m())); log("xs", xs)
    win.act_selection_pane()
def s4():
    shot("selpane")
    o = arrange.all_objects(m())[0]; docapi.controller(m()).select(o); st['o']=o
    # click it to get state
    win.update_object_tabs()
def s5():
    lo = win.layout_options; lo.rect = lo.rect or (100,100,80,60)
    log("rotatable", lo.rotatable, lo.handles_ok)
    lo._rotate(m(), st['o'], math.radians(30))
def s6(): log("angle", st['o'].RotateAngle); shot("rot"); app.quit()
import math
steps(s0, s1, s2, s3, s4, s5, s6, delay=1800)
