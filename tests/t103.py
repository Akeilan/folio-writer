import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
from folio import charts, docapi
A = win.actions; m = lambda: win.engine.model
st = {}
def s0(): win.unmaximize(); win.resize(1590,960); win.move(0,0); A.insert_text("Charts\n"); st['o'] = charts.insert_chart(m(), charts.BOX); charts.refresh(st['o'])
def s1(): shot("box"); o = st['o']; charts.set_type(o, charts.FUNNEL); charts.refresh(o); log("funnel", charts.type_index(o))
def s2(): shot("funnel"); o = st['o']; st['o'] = charts.set_type(o, charts.TREEMAP); log("tm", st['o'].Name)
def s3():
    shot("treemap"); o = st['o']; docapi.controller(m()).select(o); win.update_object_tabs()
    charts.set_type(o, charts.SUNBURST); log("idx", charts.type_index(o))
def s4(): shot("sunburst"); app.quit()
steps(s0, s1, s2, s3, s4, delay=2000)
