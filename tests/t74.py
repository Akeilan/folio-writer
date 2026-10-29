import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
from folio import drawing, docapi
A = win.actions; m = lambda: win.engine.model
def s0(): A.insert_text("x"); drawing.insert_shape(m(), "pentagon", 1, 3000, 4000, 4000, 3000)
def s1(): win.update_object_tabs()
def s2(): from folio import objecttools as OT; log("rect", OT.object_rect(win), drawing.selected_shape(m())); win.act_edit_points(); log("active", win.edit_points.active, win.edit_points.prop, len(list(win.edit_points._vertices())))
def s3():
    ep = win.edit_points; i,j,p = list(ep._vertices())[0]; x,y = ep._to_px(p)
    class E: pass
    e=E(); e.button=1; e.x=x; e.y=y; ep._press(None,e); e.x=x+60; e.y=y-40; ep._motion(win.engine.view,e); ep._release(None,e)
def s4(): shot("editpts"); app.quit()
steps(s0, s1, s2, s3, s4, delay=1500)
