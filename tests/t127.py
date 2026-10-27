exec(open("/home/claude/folio2/tests/common.py").read())
from folio import docapi
e = win.engine; m = lambda: e.model
def scr(x, y):
    ok, ox, oy = e.view.get_window().get_origin(); return int(ox + x), int(oy + y)
def clk(xt, yt, n=2):
    x, y = e.twips_to_px(xt, yt); sx, sy = scr(x, y); log("click px", x, y, "screen", sx, sy, "n", n)
    subprocess.run(["xdotool", "mousemove", str(sx), str(sy), "click", "--repeat", str(n), "--delay", "80", "1"])
def r(): return e.page_rects()[0]
def s0(): win.actions.insert_text("Body text on the page."); clk(r()[0] + r()[2] / 2, r()[1] + 3000, 1)
def s1(): clk(r()[0] + r()[2] / 2, r()[1] + 500)
def s2():
    ps = docapi.page_style(m())
    log("header dbl: in hf", win.in_header_footer(), "HeaderIsOn", ps.HeaderIsOn, "top", ps.TopMargin, "hh", ps.HeaderHeight)
    win.actions.insert_text("My header")
def s3(): shot("t127a"); clk(r()[0] + r()[2] / 2, r()[1] + 4000, 1)
def s4(): log("single body click while in header: in hf", win.in_header_footer())
def s5(): clk(r()[0] + r()[2] / 2, r()[1] + 4000)
def s6(): log("dbl body: in hf", win.in_header_footer(), repr(docapi.page_style(m()).HeaderText.getString()))
def s7(): clk(r()[0] + r()[2] / 2, r()[1] + 400, 1)
def s8(): log("single header click from body: in hf", win.in_header_footer())
def s9():
    a = win.canvas.get_vadjustment(); a.set_value(a.get_upper() - a.get_page_size()); pump(0.5)
    clk(r()[0] + r()[2] / 2, r()[1] + r()[3] - 500)
def s10(): log("footer dbl: in hf", win.in_header_footer(), docapi.page_style(m()).FooterIsOn); shot("t127b")
def s11():
    from folio import hfedit
    GLib.timeout_add(1200, lambda: (shot("t127c"), subprocess.run(["xdotool","key","Escape"]), False)[2])
    hfedit.format_dialog(win)
def s12():
    win.hf_checks["show_text"].set_active(False) if hasattr(win.hf_checks["show_text"], "set_active") else None
    win.run(("hf-option", "show_text"))
def s13(): shot("t127d"); app.quit()
steps(s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12, s13, delay=1500)
