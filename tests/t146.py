import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
from folio import docapi, drawing, insertextras
e = win.engine; m = lambda: e.model
def s0():
    e.view.set_zoom(1.0)
    insertextras.insert_textbox(m(), "simple")
    insertextras.insert_textbox(m(), "simple")
def s1():
    fr = m().getTextFrames()
    a, b = fr.getByIndex(0), fr.getByIndex(1)
    a.getText().setString(" ".join("Word%d" % i for i in range(120)))
    b.getText().setString("")
    b.HoriOrientPosition = 3000; b.VertOrientPosition = 9000
    docapi.controller(m()).select(a)
    log("names", a.Name, b.Name)
def s2():
    win.update_object_tabs()
    win.text_linker.create()
    log("pending", win.text_linker.pending)
    src = win.text_linker.src
    win.text_linker.src = None
    b = m().getTextFrames().getByIndex(1)
    docapi.controller(m()).select(b)
    win.text_linker._finish(src)
def s3():
    fr = m().getTextFrames()
    log("chain", fr.getByIndex(0).ChainNextName, fr.getByIndex(1).ChainPrevName)
    shot("t146a")
    docapi.controller(m()).select(fr.getByIndex(0))
def s4():
    win.text_linker.break_link()
    log("after break", repr(m().getTextFrames().getByIndex(0).ChainNextName))
    win.object_call_module("textlinks", "set_direction", 2)
    win.object_call_module("textlinks", "set_align", "CENTER")
    o = m().getTextFrames().getByIndex(0)
    log("dir", o.WritingMode, o.TextVerticalAdjust.value)
    app.quit()
steps(s0, s1, s2, s3, s4, delay=1500)
