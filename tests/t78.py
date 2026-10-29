import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
from folio import styletools, docapi
A = win.actions; m = lambda: win.engine.model
def s0(): win.unmaximize(); win.resize(1590,960); win.move(0,0); A.insert_text("Hello styled world")
def s1(): win.engine.command(".uno:SelectAll"); win.engine.command(".uno:Bold"); win.engine.command(".uno:CenterPara")
def s2():
    win.act_style_inspector(); rc=docapi.read_cursor(m()); vc=rc.getText().createTextCursorByRange(rc.getStart()); vc.goRight(1,True); log([(p, str(vc.getPropertyState(p).value)) for p in ("CharWeight","ParaAdjust","CharFontName")], vc.CharWeight, vc.ParaAdjust); log(styletools.direct_formatting(m()))
def s3(): shot("inspector")
def s4():
    p = [p for c,p in win.panes.items() if c.__name__=="StyleInspector"][0]; p.clear_char(); p.clear_para()
def s5(): log("after", styletools.direct_formatting(m())); 
def s6():
    GLib.timeout_add(1500, lambda: (shot("manage"), [w.response(Gtk.ResponseType.CANCEL) for w in Gtk.Window.list_toplevels() if isinstance(w, Gtk.Dialog)], False)[2])
    styletools.manage_styles(win)
def s7(): app.quit()
steps(s0, s1, s2, s3, s4, s5, s6, s7, delay=1500)
