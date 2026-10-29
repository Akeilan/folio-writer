import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
from gi.repository import LOKDocView
A = win.actions; st = {}
def s0():
    win.unmaximize(); win.resize(1590,960); win.move(0,0)
    A.insert_text("Hello"); log("s0 done")
def s1():
    try:
        log("creating"); v2 = LOKDocView.View.new_from_widget(win.engine.view, "{}")
        st["v2"] = v2; log("v2 ok", v2)
        sw = Gtk.ScrolledWindow(); sw.add(v2); sw.set_size_request(-1, 300)
        win.canvas_overlay.get_parent().pack_start(sw, False, False, 0); sw.show_all()
        v2.set_zoom(1.0)
    except Exception as e:
        log("v2 err", e)
def s2():
    vs = win.engine.model.getCurrentController().getViewSettings()
    log("vs props", [p.Name for p in vs.getPropertySetInfo().getProperties() if "Layout" in p.Name or "Book" in p.Name])
    shot("split")
def s3():
    try:
        vs = win.engine.model.getCurrentController().getViewSettings(); vs.ViewLayoutColumns = 2; win.engine.view.set_zoom(0.6)
    except Exception as e: log("cols err", e)
def s4(): log("rects", win.engine.page_rects()[:3]); shot("multipage"); app.quit()
steps(s0, s1, s2, s3, s4, delay=3000)
