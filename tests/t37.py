import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
import subprocess
def x(*a): subprocess.run(["xdotool"] + list(a), env=dict(os.environ, DISPLAY=":99"))
A = win.actions
def s0(): win.present(); win.focus_document(); A.insert_text("Bold source text. "); 
def s1(): A.cmd(".uno:SelectAll"); A.cmd(".uno:Bold")
def s1b(): A.run("copy")
def s2(): A.cmd(".uno:GoToEndOfDoc"); A.cmd(".uno:InsertPara"); A.cmd(".uno:Bold"); A.insert_text("x")
def s2b(): A.run("paste")
def s3(): log("text", repr(win.engine.model.getText().getString())); shot("paste1"); log("visible", win.paste_options.visible, win.paste_options.cursor); x("key", "ctrl")
def s4(): shot("paste2"); x("key", "t")
def s5():
    en = win.engine.model.getText().createEnumeration(); out=[]
    while en.hasMoreElements():
        p = en.nextElement(); out.append((p.getString(), p.CharWeight))
    log(out); x("type", "abc")
def s6(): log("after typing visible", win.paste_options.visible); app.quit()
steps(s0, s1, s1b, s2, s2b, s3, s4, s5, s6, delay=2000)
