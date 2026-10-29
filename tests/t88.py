import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
import subprocess, time
from folio import docapi, objecttools
A = win.actions; m = lambda: win.engine.model
T = {"draw": 0.0, "n": 0}
orig = objecttools.LayoutOptions._draw_handles
def timed(self, view, cr):
    t = time.time(); r = orig(self, view, cr); T["draw"] += time.time() - t; T["n"] += 1; return r
objecttools.LayoutOptions._draw_handles = timed
def s0(): win.unmaximize(); win.resize(1590,960); win.move(0,0); A.insert_text("Text before. More words to drop the picture into. "); docapi.insert_picture(m(), "/tmp/pic.png")
def s1():
    win.update_object_tabs(); log("rect", objecttools.object_rect(win), "sel", win.engine.selection_type() if hasattr(win.engine,'selection_type') else '')
def s2():
    r = objecttools.object_rect(win)
    if not r: log("no rect"); return
    x, y, w, h = r
    ox, oy = win.engine.view.translate_coordinates(win, 0, 0)
    wx, wy = win.get_position()
    sx, sy = int(wx + ox + x + w), int(wy + oy + y + h)
    st["start"] = (sx, sy)
    T["draw"] = 0; T["n"] = 0
    subprocess.run(["xdotool", "mousemove", str(sx), str(sy), "mousedown", "1"])
    for i in range(1, 21):
        subprocess.run(["xdotool", "mousemove", str(sx + i * 6), str(sy + i * 3)])
        time.sleep(0.02)
        while Gtk.events_pending(): Gtk.main_iteration()
    shot("middrag")
def s3():
    sx, sy = st["start"]
    subprocess.run(["xdotool", "mouseup", "1"])
    log("draw time", round(T["draw"], 3), "calls", T["n"])
def s4():
    shot("afterdrag"); log("rect after", win.layout_options.rect)
    from folio import drawing
    o = drawing.selected_shape(m()); log("size", o and (o.Size.Width, o.Size.Height))
def s5():
    # move the picture (inline) to the start of the text
    r = win.layout_options.rect; x, y, w, h = r
    ox, oy = win.engine.view.translate_coordinates(win, 0, 0); wx, wy = win.get_position()
    sx, sy = int(wx+ox+x+w/2), int(wy+oy+y+h/2)
    subprocess.run(["xdotool","mousemove",str(sx),str(sy),"mousedown","1"])
    tgt_y = wy + oy + y - 6
    for i in range(1, 15):
        subprocess.run(["xdotool","mousemove",str(sx - i*10),str(int(sy + (tgt_y - sy)*i/14))]); time.sleep(0.02)
        while Gtk.events_pending(): Gtk.main_iteration()
    shot("midmove")
    subprocess.run(["xdotool","mouseup","1"])
def s6(): log("text", repr(m().getText().getString())); shot("aftermove"); app.quit()
st = {}
steps(s0, s1, s2, s3, s4, s5, s6, delay=1800)
