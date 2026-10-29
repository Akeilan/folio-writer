import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
from folio import docapi
from folio.customize import catalog
e = win.engine; m = lambda: e.model
def s0():
    win.actions.insert_text("Bold source here and target one and target two.")
    vc = docapi.view_cursor(m()); vc.gotoStart(False); vc.goRight(4, True); vc.CharWeight = 150.0
    vc.gotoStart(False); vc.goRight(2, False)
def s1():
    c = catalog(win)["Home|Format Painter"][2]
    a = c.get_allocation(); ok, ox, oy = c.get_window().get_origin()
    x, y = ox + a.x + a.width // 2, oy + a.y + a.height // 2
    subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "--repeat", "2", "--delay", "90", "1"])
def s2(): log("painter state after dbl", e.get(".uno:FormatPaintbrush"))
def clickword(n):
    def f():
        vc = docapi.view_cursor(m())
        txt = m().getText().getString(); i = txt.find("target") if n == 1 else txt.rfind("target")
        # click via engine at the word position
        vc.gotoStart(False); vc.goRight(i + 2, False)
        x, y = win._follow_rect[0], win._follow_rect[1] + 100
        e.click_at(x, y)
    return f
def s5(): log("painter state after 2 uses", e.get(".uno:FormatPaintbrush")); app.quit()
steps(s0, s1, s2, clickword(1), clickword(2), s5, delay=1500)
