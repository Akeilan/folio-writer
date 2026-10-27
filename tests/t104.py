exec(open("/home/claude/folio2/tests/common.py").read())
from folio import charts, docapi
A = win.actions; m = lambda: win.engine.model
st = {}
def s0(): win.unmaximize(); win.resize(1590,960); win.move(0,0); A.insert_text("Charts\n"); st['o'] = charts.insert_chart(m(), 0)
def s1():
    o = st['o']; charts.set_filter(o, ["Series 2"], ["Category 3"]); charts.refresh(o)
    log("shown", list(charts.chart_doc(o).getData().getColumnDescriptions()), "full", charts.get_data(o)["cols"])
def s2():
    o = st['o']; docapi.controller(m()).select(o); win.update_object_tabs()
    P = charts.ChartFormatPane.make(win); win._chart_pane_cls = P; p = win.show_pane(P)
    p.combo.set_active(1); p.set("FillColor", 0xF2F2F2); p.combo.set_active(6); p.set("FillColor", 0xC00000)
def s3(): shot("chartfmt"); app.quit()
steps(s0, s1, s2, s3, delay=2000)
