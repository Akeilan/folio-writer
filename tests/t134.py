exec(open("/home/claude/folio2/tests/common.py").read())
from folio import docapi
e = win.engine; m = lambda: e.model
adj = win.canvas.get_vadjustment()
cc = []
import time
T0=[time.time()]
e.view.connect("cursor-changed", lambda v,x,y,w,h: cc.append((round(time.time()-T0[0],2),x,y)))
orig_click = e.click_at
def logged_click(x, y): cc.append(("CLICK", round(time.time()-T0[0],2), x, y)); orig_click(x, y)
e.click_at = logged_click
from folio import docapi as D
orig_en = D.enable_header_footer
def logged_en(*a, **k): cc.append(("ENABLE", round(time.time()-T0[0],2))); return orig_en(*a, **k)
D.enable_header_footer = logged_en
def scr(x, y):
    ok, ox, oy = e.view.get_window().get_origin(); return int(ox + x), int(oy + y)
def clk(xt, yt, n=2):
    x, y = e.twips_to_px(xt, yt); sx, sy = scr(x, y - adj.get_value() * 0)
    subprocess.run(["xdotool", "mousemove", str(sx), str(sy), "click", "--repeat", str(n), "--delay", "80", "1"])
def s0():
    for i in range(3):
        win.actions.apply_style("Heading 1"); win.actions.insert_text("Heading %d" % (i + 1)); e.command(".uno:InsertPara")
        win.actions.apply_style("Normal"); win.actions.insert_text("Page %d text." % (i + 1)); e.command(".uno:InsertPagebreak")
    win.actions.insert_text("Last.")
    pass
def s1():
    adj.set_value(0); pump(0.5); cc.clear(); T0[0]=time.time()
    r = e.page_rects()[0]; log("rects", e.page_rects()); clk(r[0] + r[2] / 2, r[1] + 500)
def s2():
    log("in hf", win.in_header_footer(), "cursor events", cc, "adj", adj.get_value(), "page", docapi.read_cursor(m()).getPage())
def s2b():
    # move the mouse over the page, as a user would
    for dx in (0, 40, 80, 120):
        ok, ox, oy = e.view.get_window().get_origin()
        subprocess.run(["xdotool", "mousemove", str(ox + 300 + dx), str(oy + 300)]); pump(0.2)
def s2c(): log("after mouse moves: adj", adj.get_value(), "last cursor", cc[-1:])
def s3():
    cc.clear(); r = e.page_rects()[0]; clk(r[0] + r[2] / 2 + 2000, r[1] + 900, 1)
def s4():
    log("single click p1 while in hf: events", cc[-4:], "page", docapi.read_cursor(m()).getPage(), "adj", adj.get_value())
steps(s0, s1, s2, s2b, s2c, s3, s4, lambda: (shot("t134"), app.quit()), delay=2000)
