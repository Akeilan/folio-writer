exec(open("/home/claude/folio2/tests/common.py").read())
from folio import compat, insertextras
from gi.repository import GLib
e = win.engine; m = lambda: e.model; A = win.actions
def s0():
    A.insert_text("Hi ")
    win.eqbar.new_equation("a/b"); win.eqbar.finish()
    insertextras.insert_textbox(m(), "simple"); insertextras.insert_textbox(m(), "simple")
def s1():
    fr = m().getTextFrames(); fr.getByIndex(0).ChainNextName = fr.getByIndex(1).Name
    log("ch", [(n, m().getTextFrames().getByName(n).ChainNextName) for n in m().getTextFrames().getElementNames()])
    f = compat.scan(m()); log("found", f)
    log("doc", compat.issues_for(f, "doc")); log("odt", compat.issues_for(f, "odt"))
def s2():
    def close():
        for w in Gtk.Window.list_toplevels():
            if isinstance(w, Gtk.Dialog) and w.get_visible():
                shot("t149a"); log("dialog", w.get_title()); w.response(Gtk.ResponseType.CANCEL)
        return False
    GLib.timeout_add(1500, close)
    ok = win.save_to("/tmp/t149.doc")
    log("saved?", ok)
    app.quit()
steps(s0, s1, s2, delay=1500)
