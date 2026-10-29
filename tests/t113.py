import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
from folio import docapi
A = win.actions
adj = win.canvas.get_vadjustment()
win.connect("key-press-event", lambda w,e: log("KEY", Gdk.keyval_name(e.keyval), int(e.state)))
from gi.repository import Gdk
def s0():
    for i in range(60):
        A.insert_text("Paragraph %d with some text. " % i * 4)
        win.engine.command(".uno:InsertPara")
    win.engine.view.grab_focus()
def chk(n): return lambda: log(n, adj.get_value(), docapi.read_cursor(win.engine.model).getPosition().Y, win.get_focus(), win.is_active())
def key(k): return lambda: subprocess.Popen(["xdotool", "key", k])
steps(s0, chk("a"), key("ctrl+Home"), chk("b"), lambda: win.engine.command(".uno:GoToStartOfDoc"), chk("b2"), lambda: log("uno ok", docapi.read_cursor(win.engine.model).getPosition().Y), key("Down"), chk("c"), key("ctrl+End"), chk("d"), key("ctrl+Home"), chk("e"), lambda: app.quit(), delay=700)
