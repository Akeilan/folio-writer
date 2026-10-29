import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
from folio import docapi
e = win.engine; m = lambda: e.model; ed = win.eqbar.ed
def scr(x, y):
    ok, ox, oy = e.view.get_window().get_origin(); return int(ox + x), int(oy + y)
def key(*k): return lambda: subprocess.run(["xdotool", "key", "--delay", "80"] + list(k))
def s0():
    win.actions.insert_text("Inline ")
    win.eqbar.new_equation("x^2"); win.eqbar.finish()
    win.actions.insert_text(" text after.")
def s1():
    vc = docapi.view_cursor(m()); vc.gotoStart(False); vc.goRight(7, False)
def s2(): log("before right: active", ed.active)
def s3():
    log("after right: active", ed.active, "caret", ed.caret[1], "display", ed._display())
    a = ed.obj.getAnchor(); log("adj", repr(a.ParaAdjust), ed._alone())
    from folio import eqnumber; log("num", repr(eqnumber.current(ed.obj)))
def s4():
    fx, fy, w, h = ed.frame
    tx, ty, th = ed._tab_rect(); sx, sy = scr(tx + 7, ty + th/2)
    subprocess.run(["xdotool", "mousemove", str(sx), str(sy), "click", "1"])
def s5(): shot("t126menu"); subprocess.run(["xdotool", "key", "Escape"])
def opt():
    GLib.timeout_add(1500, lambda: (shot("t126opt"), subprocess.run(["xdotool", "key", "Escape"]), False)[2])
    win.eqbar.options_dialog()
def ink():
    def draw():
        ok, ox, oy = win.get_window().get_origin()
        shot("t126ink0")
        subprocess.run(["xdotool", "key", "Escape"])
        return False
    GLib.timeout_add(1500, draw)
    win.eqbar.ink_equation()
steps(s0, s1, s2, key("Right"), s3, s4, s5, key("Escape"), opt, ink, lambda: app.quit(), delay=1500)
