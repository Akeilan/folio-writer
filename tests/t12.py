exec(open("/home/claude/folio2/tests/common.py").read())
import subprocess
e = win.engine
def x(*a): subprocess.run(["xdotool"] + list(a), env=dict(os.environ, DISPLAY=":99"))
def s0(): win.present(); win.actions.insert_text("Paragraph text that will wrap around shapes. " * 6)
def s1(): win.run(("draw-shape", "ellipse"))
def s2(): x("mousemove", "450", "450", "mousedown", "1", "mousemove", "550", "520", "mousemove", "600", "560", "mouseup", "1")
def s3(): x("mousemove", "300", "800", "click", "1")
def s4(): x("mousemove", "520", "500", "click", "1")
def s5():
    log("shape tab:", win.ribbon.tab_by_name("Shape Format").button.get_visible())
    win.object_call("set_fill", 0xC00000); win.object_call("set_outline", 0x000000, 3)
def s6():
    x("mousemove", "300", "800", "click", "1")
    from folio import docapi
    GLib.timeout_add(500, lambda: (docapi.insert_picture(e.model, "/tmp/pic.png"), win.update_object_tabs(), False)[2])
def s7():
    log("pic tab:", win.ribbon.tab_by_name("Picture Format").button.get_visible(), "shape tab", win.ribbon.tab_by_name("Shape Format").button.get_visible())
    win.update_object_tabs()
    log("pic tab after update:", win.ribbon.tab_by_name("Picture Format").button.get_visible())
    win.object_call("set_wrap", "square")
def s8(): shot("t12"); app.quit()
steps(s0, s1, s2, s3, s4, s5, s6, s7, s8, delay=1500)
