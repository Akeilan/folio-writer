import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
from folio import docapi
e = win.engine; m = lambda: e.model; A = win.actions
def s0():
    A.insert_text("Text with fraction ")
    win.eqbar.new_equation("a/b"); win.eqbar.finish()
    A.insert_text(" and script ")
    win.eqbar.new_equation("x_i^2"); win.eqbar.finish()
    A.insert_text(" and plain ")
    win.eqbar.new_equation("x+y"); win.eqbar.finish()
    A.insert_text(" end of line.")
def s1():
    for o in docapi.formulas(m()):
        emb = o.getEmbeddedObject()
        log(docapi.formula_of(o), "size", o.Size.Width, o.Size.Height, "base", emb.BaseFontHeight, "vert", getattr(o, "VertOrient", None))
    shot("t136")
steps(s0, s1, lambda: app.quit(), delay=2500)
