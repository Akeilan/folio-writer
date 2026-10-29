import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
from folio import docapi
A = win.actions; m = lambda: win.engine.model
def s0():
    win.unmaximize(); win.resize(1590,960); win.move(0,0)
    A.apply_style("Heading 1"); A.insert_text("Chapter One"); win.engine.command(".uno:InsertPara")
    A.apply_style("Normal"); A.insert_text("Body of chapter one. " * 10); win.engine.command(".uno:InsertPara")
    A.apply_style("Heading 2"); A.insert_text("Section 1.1"); win.engine.command(".uno:InsertPara")
    A.apply_style("Normal"); A.insert_text("Body of section."); win.engine.command(".uno:InsertPara")
    A.apply_style("Heading 1"); A.insert_text("Chapter Two"); win.engine.command(".uno:InsertPara")
    A.apply_style("Normal"); A.insert_text("Body two.")
def s1():
    from folio import app as appmod
    try:
        app.apply_engine_config({("Writer/Content/Display", "ShowOutlineContentVisibilityButton"): "true"}) if hasattr(app,'apply_engine_config') else None
    except Exception as e: log("cfg", e)
    from folio import bridge
    cp = bridge.create("com.sun.star.configuration.ConfigurationProvider")
    ua = cp.createInstanceWithArguments("com.sun.star.configuration.ConfigurationUpdateAccess", (bridge.prop("nodepath", "/org.openoffice.Office.Writer/Content/Display"),))
    ua.ShowOutlineContentVisibilityButton = True; ua.commitChanges()
    vc = docapi.view_cursor(m()); vc.gotoStart(False)
    win.engine.command(".uno:ToggleOutlineContentVisibility")
def s2():
    shot("fold"); log("pages", win.engine.get(".uno:StatePageNumber"))
    en = m().getText().createEnumeration(); out=[]
    while en.hasMoreElements():
        p = en.nextElement()
        try: out.append([g.Name+"="+str(g.Value) for g in p.ParaInteropGrabBag])
        except Exception as e: out.append(str(e)[:30])
    log(out); app.quit()
steps(s0, s1, s2, delay=1800)
