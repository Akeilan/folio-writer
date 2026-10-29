import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
A = win.actions; m = lambda: win.engine.model
def s0(): A.cmd(".uno:FontDialog") if False else None; A.insert_text("Plain start. ")
HTML = '<html><body><p><span style="font-family:Courier New;font-size:20pt;color:red">Big red <b>bold</b> words</span></p></body></html>'
def s1(): A._clipboard_html = lambda: HTML; A.default_paste_mode = lambda: "merge"
def s2(): A.do_paste()
def s3(): log("text", repr(m().getText().getString()))
def s4():
    en = m().getText().createEnumeration(); out=[]
    while en.hasMoreElements():
        p = en.nextElement(); r = p.createEnumeration()
        while r.hasMoreElements():
            x = r.nextElement(); out.append((x.getString(), x.CharFontName, x.CharHeight, x.CharWeight))
    log("merged", out); app.quit()
from gi.repository import Gdk
steps(s0, s1, s2, s3, s4, delay=2000)
