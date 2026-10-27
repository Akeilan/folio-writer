exec(open("/home/claude/folio2/tests/common.py").read())
import subprocess, time, traceback
from folio import docapi
A = win.actions; m = lambda: win.engine.model
adj = win.canvas.get_vadjustment()
st = {"last": 0}
def changed(a):
    v = a.get_value()
    if st["last"] > 500 and v < 50:
        log("JUMP TO TOP from", st["last"], "".join(traceback.format_stack(limit=12)[-10:]))
    st["last"] = v
adj.connect("value-changed", changed)
win.engine.view.connect("cursor-changed", lambda v,x,y,w,h: log("cursor-changed", x,y,w,h, adj.get_value()) if st.get("watch") else None)
orig_vc = docapi.view_cursor
def vc_logged(mm):
    if st.get("watch"):
        log("view_cursor called:", "".join(traceback.format_stack(limit=6)[-5:-1]))
    return orig_vc(mm)
docapi.view_cursor = vc_logged
def s0():
    win.unmaximize(); win.resize(1590,960); win.move(0,0)
    for i in range(60):
        A.insert_text("Paragraph %d with some text that goes on for a while to fill the line. " % i * 2)
        win.engine.command(".uno:InsertPara")
def s1():
    win.engine.view.grab_focus()
    subprocess.run(["xdotool", "key", "ctrl+End"]); time.sleep(0.5)
    while Gtk.events_pending(): Gtk.main_iteration()
    log("after ctrl+end", adj.get_value(), adj.get_upper(), docapi.read_cursor(m()).getPage(), win.engine.get(".uno:StatePageNumber"), win.get_focus())
    shot("t110a"); st["watch"] = True
    for i in range(30):
        subprocess.run(["xdotool", "key", "Up"]); time.sleep(0.05)
        while Gtk.events_pending(): Gtk.main_iteration()
        if i % 10 == 0: log("up", i, adj.get_value())
    log("adj", adj.get_value())
def s2():
    for i in range(10):
        subprocess.run(["xdotool", "key", "Down"]); time.sleep(0.05)
        while Gtk.events_pending(): Gtk.main_iteration()
    log("adj2", adj.get_value()); app.quit()
steps(s0, s1, s2, delay=4000)
