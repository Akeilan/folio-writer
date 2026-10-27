exec(open("/home/claude/folio2/tests/common.py").read())
import subprocess
def x(*a): subprocess.run(["xdotool"] + list(a), env=dict(os.environ, DISPLAY=":99"))
def s0(): win.present(); win.actions.insert_text("Select some of these words with the mouse please.")
def s1(): x("mousemove", "360", "341", "mousedown", "1", "mousemove", "420", "341", "mousemove", "480", "341", "mouseup", "1")
def s2(): shot("t17"); app.quit()
steps(s0, s1, s2, delay=1500)
