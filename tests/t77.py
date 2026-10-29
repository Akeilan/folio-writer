import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
from folio import charts, docapi
A = win.actions; m = lambda: win.engine.model
st = {}
def s0(): A.insert_text("Chart test.\n"); st['o'] = charts.insert_chart(m(), 0)
def s1():
    o = st['o']; charts.set_type(o, 5)
    cd = charts.chart_doc(o); log("type", cd.getDiagram().getDiagramType())
    log("loaded", o.getExtendedControlOverEmbeddedObject().getCurrentState() if hasattr(o.getExtendedControlOverEmbeddedObject(),'getCurrentState') else '?')
    import uno
    for name in (".uno:UpdateAll", ".uno:Repaint"):
        pass
    o2 = charts.chart_doc(o); log("same", o2 == cd, o2.getDiagram().getDiagramType())
    xo = o.getExtendedControlOverEmbeddedObject()
    try:
        xo.changeState(2); log("ui-active"); 
    except Exception as e: log("cs", e)
def s2():
    o=st['o']; xo = o.getExtendedControlOverEmbeddedObject()
    try: xo.changeState(1); log("back running")
    except Exception as e: log("cs2", e)
def s3(): shot("r1"); app.quit()
steps(s0, s1, s2, s3, delay=2000)
