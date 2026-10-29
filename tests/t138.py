import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
import subprocess, time
from folio import docapi, drawing
m = lambda: win.engine.model
def scr(x, y):
    ox, oy = win.engine.view.translate_coordinates(win, 0, 0); wx, wy = win.get_position(); return int(wx+ox+x), int(wy+oy+y)
def drag(hx, hy, dx, dy):
    sx, sy = scr(hx, hy)
    subprocess.run(["xdotool","mousemove",str(sx),str(sy),"mousedown","1"])
    for i in range(1, 11):
        subprocess.run(["xdotool","mousemove",str(sx+dx*i//10),str(sy+dy*i//10)]); time.sleep(0.02)
        while Gtk.events_pending(): Gtk.main_iteration()
    sel = docapi.controller(m()).getSelection()
    log("sel before up", sel.getImplementationName() if sel else None, "drag", win.layout_options.drag and win.layout_options.drag.get("handle"))
    subprocess.run(["xdotool","mouseup","1"])
def s0():
    win.unmaximize(); win.resize(1590,960); win.move(0,0)
    win.actions.apply_style("Heading 1"); win.actions.insert_text("A heading"); win.engine.command(".uno:InsertPara"); win.actions.apply_style("Normal")
    for i in range(30): win.actions.insert_text("Filler line %d. " % i * 6); win.engine.command(".uno:InsertPara")
    win.actions.insert_text("Picture test paragraph. "); docapi.insert_picture(m(), "/tmp/pic.png")
    win.actions.insert_text(" after.")
def s1():
    g = m().getGraphicObjects().getByIndex(0); st["g"] = g
    log("anchor", g.AnchorType.value, "size", g.Size.Width, g.Size.Height)
    docapi.select_object(m(), g)
def s2():
    win.engine.view.set_zoom(1.5); pump(1.0)
    g = st["g"]; g.AnchorType = __import__("folio.bridge", fromlist=["x"]).enum("com.sun.star.text.TextContentAnchorType", "AT_PARAGRAPH")
    docapi.select_object(m(), g); pump(1.0)
    win.update_object_tabs()
def s2b():
    r = win.layout_options.rect
    a = win.canvas.get_vadjustment(); a.set_value(max(0, r[1] - 150)); pump(0.8)
    log("scrolled", a.get_value())
def s3():
    shot("t138pre"); lo = win.layout_options; r = lo.rect; log("rect", r, "handles_ok", lo.handles_ok, "active", lo._active(), "visible", lo.visible)
    if r: x,y,w,h = r; drag(x+w, y+h, 60, 60)
def s4():
    g = st["g"]; log("after corner", g.Size.Width, g.Size.Height, "ratio", round(g.Size.Width/g.Size.Height, 3)); shot("t138a")
    r = win.layout_options.rect; log("rect2", r)
    if r: x,y,w,h = r; drag(x+w, y+h/2, -80, 0)
def s5():
    g = st["g"]; log("after side", g.Size.Width, g.Size.Height); shot("t138b"); app.quit()
st = {}
steps(s0, s1, s2, s2b, s3, s4, s5, delay=1800)
