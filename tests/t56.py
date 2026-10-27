exec(open("/home/claude/folio2/tests/common.py").read())
import subprocess
def x(*a): subprocess.run(["xdotool"] + list(a), env=dict(os.environ, DISPLAY=":99"))
def s0(): win.unmaximize(); win.resize(1590,960); win.move(0,0); win.present(); win.focus_document(); win.actions.insert_text("Hello world")
def s1(): log("zoom0", win.engine.view.get_zoom()); x("mousemove", "800", "500"); x("keydown", "ctrl"); x("click", "4"); x("click", "4"); x("keyup", "ctrl")
def s2(): log("zoom after ctrl-wheel", win.engine.view.get_zoom()); x("key", "shift+F10")
def s3():
    menus = [w for w in Gtk.Window.list_toplevels() if w.get_visible() and w.get_type_hint() in (Gdk.WindowTypeHint.POPUP_MENU, Gdk.WindowTypeHint.DROPDOWN_MENU)]
    log("menu open", len(menus)); shot("ctxmenu"); x("key", "Escape")
def s4(): x("key", "F6")
def s5(): log("after F6 keytips", win.keytips.active); x("key", "F6")
def s6(): log("after F6 focus", type(win.get_focus()).__name__, win.get_focus().is_ancestor(win.status) if win.get_focus() else None); x("key", "F6")
def s7(): log("after F6 back", win.get_focus() is win.engine.view); app.quit()
from gi.repository import Gdk
steps(s0, s1, s2, s3, s4, s5, s6, s7, delay=1500)
