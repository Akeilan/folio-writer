exec(open("/home/claude/folio2/tests/common.py").read())
import subprocess
def x(*a): subprocess.run(["xdotool"] + list(a), env=dict(os.environ, DISPLAY=":99"))
def s0(): win.present(); win.focus_document()
def s1(): x("type", "--delay", "60", "--", "Smile :) frown :( ")
def s2():
    log(repr(win.engine.model.getText().getString()))
    from folio.options import autocorrect_dialog
    GLib.timeout_add(1500, lambda: (shot("acdlg"), [w.response(Gtk.ResponseType.CANCEL) for w in Gtk.Window.list_toplevels() if isinstance(w, Gtk.Dialog) and w.get_visible()], False)[2])
    autocorrect_dialog(win)
def s3(): shot("smile"); app.quit()
steps(s0, s1, s2, s3, delay=3000)
