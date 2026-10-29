import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
from folio import docapi
e = win.engine; m = lambda: e.model; A = win.actions
def s0():
    A.insert_text("Base xx ")
    win.eqbar.new_equation("x+y"); win.eqbar.finish()
    A.insert_text(" xx ")
    win.eqbar.new_equation("x_i^2"); win.eqbar.finish()
    A.insert_text(" xx ")
    win.eqbar.new_equation("x_i"); win.eqbar.finish()
    A.insert_text(" xx ")
    win.eqbar.new_equation("(a+b)/(c+d)"); win.eqbar.finish()
    A.insert_text(" xx end. Real  double.")

def s1():
    a = win.canvas.get_hadjustment(); a.set_value(0)
    try:
        s = m().createInstance("com.sun.star.text.DocumentSettings"); log("MathBaselineAlignment", s.MathBaselineAlignment)
    except Exception as ex: log("err", ex)
    r = e.page_rects()[0]
    surf = e.render(r[0] + 1300, r[1] + 1500, 9500, 900, 1900)
    surf.write_to_png("/tmp/t139.png")
steps(s0, lambda: None, lambda: None, s1, lambda: app.quit(), delay=2500)
