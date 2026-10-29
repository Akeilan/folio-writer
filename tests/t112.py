import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
A = win.actions
adj = win.canvas.get_vadjustment()
T0 = [time.time()]
win.engine.view.connect("cursor-changed", lambda v,x,y,w,h: log("cc %.2f" % (time.time()-T0[0]), y, adj.get_value()))
def s0():
    for i in range(60):
        A.insert_text("Paragraph %d with some text. " % i * 4)
        win.engine.command(".uno:InsertPara")
def key(k): return lambda: (subprocess.Popen(["xdotool", "key", k]), log("key", k, "%.2f" % (time.time()-T0[0])))
def chk(n): return lambda: (log(n, adj.get_value(), win.engine.get(".uno:StatePageNumber"), docapi.read_cursor(win.engine.model).getPosition().Y, win.get_focus()), shot(n))
from folio import docapi
def start(): win.connect("set-focus", lambda w, f: log("SET-FOCUS", f, "".join(traceback.format_stack(limit=14)[-12:-1])));  win.engine.view.grab_focus(); T0[0]=time.time()
fns=[s0,start,chk("start"),key("ctrl+End"),chk("end")]+[key("Up")]*20+[chk("ups")]+[key("ctrl+Home"),chk("home"),chk("home2"),chk("home3")]+[key("Down")]*40+[chk("downs")]
fns.append(lambda: app.quit())
steps(*fns, delay=250)
GLib.timeout_add(0, lambda: None)
