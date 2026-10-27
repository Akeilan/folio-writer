exec(open("/home/claude/folio2/tests/common.py").read())
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
