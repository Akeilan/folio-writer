import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
from folio import accessibility, drawing, docapi
A = win.actions; m = lambda: win.engine.model
def s0(): win.unmaximize(); win.resize(1590,960); win.move(0,0); A.insert_text("Intro"); win.run("insert-table") if False else None
def s1():
    from folio import tablestyles; tablestyles.insert_table(m(), 2, 2) if hasattr(tablestyles,'insert_table') else None
    drawing.insert_shape(m(), "rectangle", 1, 9000, 9000, 3000, 2000)
def s2():
    st = dict(app.settings.get("status_items") or {}); st.update({"line": True, "column": True, "section": True, "vpos": True, "chars": True}); app.settings["status_items"] = st; win.status.apply_items()
    docapi.view_cursor(m()).gotoStart(False); win.status.schedule_metrics(10)
def s3(): win.run("check-accessibility"); log([(c,l) for c,l,t in accessibility.check(m())])
def s4(): win.status._check_proof(); shot("a11y")
def s5(): app.settings["status_items"] = {}; app.quit()
steps(s0, s1, s2, s3, s4, s5, delay=1800)
