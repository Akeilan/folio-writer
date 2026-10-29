import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
from folio import docapi, drawing, arrange, pictools, bridge
m = lambda: win.engine.model
def s0(): win.actions.insert_text("x"); drawing.insert_shape(m(), "rectangle", 1, 3000, 15000, 4000, 3000)
def s1():
    o = arrange.all_objects(m())[0]
    import uno, traceback
    try:
        eng = bridge.create("com.sun.star.drawing.EnhancedCustomShapeEngine", bridge.prop("CustomShape", o))
        r = uno.invoke(eng, "render", ())
        log("r", r.getShapeType() if r else r)
        log("polys", pictools._polys(o)[:1])
    except Exception: log(traceback.format_exc())
    app.quit()
steps(s0, s1, delay=1500)
