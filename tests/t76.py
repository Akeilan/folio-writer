import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
from folio import charts, docapi
A = win.actions; m = lambda: win.engine.model
st = {}
def s0(): win.unmaximize(); win.resize(1590,960); win.move(0,0); A.insert_text("Chart test."); A.insert_text("\n"); st['o'] = charts.insert_chart(m(), 13)
def s1():
    st["o"] and None
    o = st['o']; charts.set_axis_titles(o, "Months", "Sales"); charts.set_data_labels(o, "outside-end"); charts.set_chart_style(o, 1)
    charts.set_gridlines(o, True, True, False, False); charts.refresh(o)
def s2(): shot("combo"); o = st['o']; charts.set_type(o, charts.WATERFALL); charts.refresh(o); log("wf", charts.get_data(o)["rows"], charts.type_index(o))
def s3(): shot("waterfall"); o = st['o']; charts.set_type(o, charts.HISTOGRAM); charts.refresh(o); log("hist", charts.chart_doc(o).getData().getRowDescriptions())
def s4(): shot("hist"); o = st['o']; charts.set_type(o, 0); charts.set_colors(o, charts.MONOCHROMATIC[0][1]); charts.quick_layout(o, 4); charts.refresh(o); log("back", charts.get_data(o)["cols"], charts.type_index(o))
def s5(): shot("mono"); docapi.controller(m()).select(st['o']); win.update_object_tabs()
def s6(): win.select_tab("Chart Design"); shot("charttab")
def s7():
    GLib.timeout_add(1500, lambda: (shot("typedlg"), [w.response(Gtk.ResponseType.CANCEL) for w in Gtk.Window.list_toplevels() if isinstance(w, Gtk.Dialog)], False)[2])
    charts.type_dialog(win, 14)
def s8(): app.quit()
steps(s0, s1, s2, s3, s4, s5, s6, s7, s8, delay=2000)
