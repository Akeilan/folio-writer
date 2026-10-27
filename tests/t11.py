exec(open("/home/claude/folio2/tests/common.py").read())
import subprocess
e = win.engine
def x(*a): subprocess.run(["xdotool"] + list(a), env=dict(os.environ, DISPLAY=":99"))
def s0(): win.present(); win.actions.insert_text("Shape test paragraph with some words.")
def s1(): win.run(("draw-shape", "star5"))
def s2(): x("mousemove", "450", "450", "mousedown", "1", "mousemove", "550", "520", "mousemove", "650", "600", "mouseup", "1")
def s3(): log("shapes", e.model.getDrawPage().getCount()); win.run(("draw-shape", "textbox"))
def s4(): x("mousemove", "450", "650", "mousedown", "1", "mousemove", "600", "700", "mousemove", "750", "730", "mouseup", "1")
def s5(): x("type", "Inside box")
def s6(): win.run(("draw-shape", "arrow-line"))
def s7(): x("mousemove", "800", "450", "mousedown", "1", "mousemove", "850", "500", "mousemove", "950", "600", "mouseup", "1")
def s8(): shot("t11b"); log("shapes", e.model.getDrawPage().getCount()); app.quit()
steps(s0, s1, s2, s3, s4, s5, s6, s7, s8, delay=1500)
