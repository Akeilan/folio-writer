import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
e = win.engine
from folio import charts, docapi, bridge
def s1():
    m = e.model
    log("a")
    obj = m.createInstance("com.sun.star.text.TextEmbeddedObject"); obj.CLSID = charts.CHART_CLSID
    obj.AnchorType = bridge.enum("com.sun.star.text.TextContentAnchorType", "AS_CHARACTER")
    vc = docapi.view_cursor(m); log("b")
    vc.getText().insertTextContent(vc, obj, False); log("c inserted")
    obj.Size = bridge.struct("com.sun.star.awt.Size", Width=15240, Height=8890); log("d sized")
    cd = obj.getEmbeddedObject(); log("e emb", cd is not None)
    log("has internal", cd.hasInternalDataProvider()); cd.createInternalDataProvider(False); log("created")
    cd.setDiagram(cd.createInstance("com.sun.star.chart.BarDiagram")); log("diagram")
    data = cd.getData(); log("f", list(data.getColumnDescriptions()))
    charts.set_data(obj, charts.DEFAULT_DATA); log("g data")
    charts.set_type(obj, 0); log("h type")
    charts.set_title(obj, "Chart Title"); log("i title")
    charts.set_legend(obj, "bottom"); log("j legend")
def s2(): shot("t13"); app.quit()
steps(s1, s2, delay=2500)
