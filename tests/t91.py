exec(open("/home/claude/folio2/tests/common.py").read())
import subprocess, time
from folio import docapi, drawing
m = lambda: win.engine.model
st = {}
def s0(): win.unmaximize(); win.resize(1590,960); win.move(0,0); win.actions.insert_text("Shape test"); drawing.insert_shape(m(), "rectangle", 1, 4000, 5000, 4000, 2000)
def s1():
    docapi.view_cursor(m()).gotoEnd(False)
    rx, ry, rw, rh = win.engine.page_rects()[0]
    px, py = win.engine.twips_to_px(rx + 6000*1440/2540, ry + 6000*1440/2540)
    ox, oy = win.engine.view.translate_coordinates(win, 0, 0); wx, wy = win.get_position()
    subprocess.run(["xdotool","mousemove",str(int(wx+ox+px)),str(int(wy+oy+py)),"click","1"])
def drag(hx, hy, dx, dy):
    ox, oy = win.engine.view.translate_coordinates(win, 0, 0); wx, wy = win.get_position()
    sx, sy = int(wx+ox+hx), int(wy+oy+hy)
    subprocess.run(["xdotool","mousemove",str(sx),str(sy),"mousedown","1"])
    for i in range(1, 11):
        subprocess.run(["xdotool","mousemove",str(sx+dx*i//10),str(sy+dy*i//10)]); time.sleep(0.02)
        while Gtk.events_pending(): Gtk.main_iteration()
    subprocess.run(["xdotool","mouseup","1"])
def s2():
    o = drawing.selected_shape(m()); log("before", o.Size.Width, o.Size.Height, o.HoriOrientPosition, o.VertOrientPosition, win.layout_options.rect)
    x,y,w,h = win.layout_options.rect; drag(x+w, y+h, 80, 20)
def s3():
    o = drawing.selected_shape(m()); log("after resize", o and (o.Size.Width, o.Size.Height))
    x,y,w,h = win.layout_options.rect; drag(x+w/2, y+h/2, 100, 60)
def s4():
    o = drawing.selected_shape(m()); log("after move", o and (o.HoriOrientPosition, o.VertOrientPosition)); shot("shape"); app.quit()
steps(s0, s1, s2, s3, s4, delay=1800)
