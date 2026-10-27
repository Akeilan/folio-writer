exec(open("/home/claude/folio2/tests/common.py").read())
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
    subprocess.run(["xdotool","mouseup","1"])
st = {}
def s0():
    win.unmaximize(); win.resize(1590,960); win.move(0,0)
    win.actions.apply_style("Heading 1"); win.actions.insert_text("Heading"); win.engine.command(".uno:InsertPara"); win.actions.apply_style("Normal")
    win.actions.insert_text("Line one of text. " * 5); win.engine.command(".uno:InsertPara")
    win.actions.insert_text("Inline picture: "); docapi.insert_picture(m(), "/tmp/pic.png")
def s1():
    g = m().getGraphicObjects().getByIndex(0); st["g"] = g; docapi.select_object(m(), g)
def s2(): win.update_object_tabs(); shot("t144a")
def s3():
    r = win.layout_options.rect; log("rect", r); x,y,w,h = r; drag(x+w, y+h, -100, -40)
def s4():
    g = st["g"]; log("after corner", g.Size.Width, g.Size.Height, "rect", win.layout_options.rect); shot("t144b"); app.quit()
steps(s0, s1, s2, s3, s4, delay=1800)
