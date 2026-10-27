exec(open("/home/claude/folio2/tests/common.py").read())
from folio import notes, docapi
A = win.actions; m = lambda: win.engine.model
def s0(): win.unmaximize(); win.resize(1590,960); win.move(0,0); A.insert_text("First sentence.")
def s1(): notes.insert_note(m(), False); A.insert_text("Footnote one.")
def s2(): docapi.view_cursor(m()).gotoEnd(False); A.insert_text(" Second.")
def s3(): notes.insert_note(m(), False, "*"); A.insert_text("Starred note.")
def s4(): notes.apply_settings(m(), False, 3, 1, 2); log("fn", [n.getLabel() or n.getAnchor().getString() for n in notes.notes(m(), False)])
def s5(): shot("fn")
def s6(): win.engine.sync(lambda: log("conv", notes.convert(m(), True), len(notes.notes(m(), False)), len(notes.notes(m(), True)), [n.getText().getString() for n in notes.notes(m(), True)]))
def s7(): shot("en")
def s8():
    GLib.timeout_add(1500, lambda: (shot("fndlg"), [w.response(Gtk.ResponseType.CANCEL) for w in Gtk.Window.list_toplevels() if isinstance(w, Gtk.Dialog)], False)[2])
    notes.dialog(win)
def s9(): app.quit()
steps(s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, delay=1500)
