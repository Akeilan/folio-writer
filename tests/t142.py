import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
from folio import docapi
e = win.engine; m = lambda: e.model; A = win.actions
def s0():
    e.view.set_zoom(2.5)
    A.insert_text("Base xx ")
    win.eqbar.new_equation("x_i^2+(a+b)/c"); win.eqbar.finish()
    A.insert_text(" xx end.")
def s1():
    o = docapi.formulas(m())[0]; win.eqbar.edit(o)
def s2():
    a = win.canvas.get_hadjustment(); a.set_value(0)
    shot("t142a")
def s3(): win.eqbar.finish()
def s4(): shot("t142b"); app.quit()
steps(s0, s1, s2, s3, s4, delay=2000)
