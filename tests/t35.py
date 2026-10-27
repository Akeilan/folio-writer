exec(open("/home/claude/folio2/tests/common.py").read())
import subprocess
def x(*a): subprocess.run(["xdotool"] + list(a), env=dict(os.environ, DISPLAY=":99"))
def spy(w, ev):
    log("key", Gdk.keyval_name(ev.keyval), ev.state, win.keymap.lookup(ev), "focus", type(win.get_focus()).__name__)
    return False
from gi.repository import Gdk
win.connect("key-press-event", spy)
def s0(): win.present(); win.focus_document(); x("type", "--delay", "60", "-x")
def s1(): log(repr(win.engine.model.getText().getString())); x("type", "--delay", "60", "y-z")
def s4(): log(repr(win.engine.model.getText().getString())); app.quit()
steps(s0, s1, s4, delay=2500)
