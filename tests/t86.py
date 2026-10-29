import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
from folio import stylemodify as SM, docapi
from gi.repository import Gdk
A = win.actions; m = lambda: win.engine.model
st = {}
def s0():
    win.unmaximize(); win.resize(1590,960); win.move(0,0)
    A.apply_style("Heading 1"); A.insert_text("A heading"); win.engine.command(".uno:InsertPara")
    A.apply_style("Normal"); A.insert_text("Body text."); win.engine.command(".uno:InsertPara")
    A.apply_style("Heading 1"); A.insert_text("Second heading")
def s1():
    # right-click the Heading 1 tile
    tiles = [b for b in win.style_gallery.items.get_children() if b.style_name == "Heading 1"]
    ev = Gdk.Event.new(Gdk.EventType.BUTTON_PRESS); ev.button = 3; ev.x = 10; ev.y = 10
    st['pop'] = SM.context_menu(win, "Heading 1", tiles[0], ev)
    log("instances", SM.count_instances(m(), "Heading 1"))
def s2(): shot("ctxmenu"); st['pop'].popdown()
def s3():
    def drive():
        dlg = [w for w in Gtk.Window.list_toplevels() if isinstance(w, Gtk.Dialog) and w.get_visible()][0]
        st['dlg'] = dlg
        # find toolbar widgets: set size via combo entries
        def walk(w, out):
            out.append(w)
            if isinstance(w, Gtk.Container):
                for c in w.get_children(): walk(c, out)
            return out
        ws = walk(dlg, [])
        entries = [w for w in ws if isinstance(w, Gtk.Entry)]
        log("entries", [e.get_text() for e in entries][:4])
        # entries: name, font, size
        entries[2].set_text("20")
        tb = [w for w in ws if isinstance(w, Gtk.ToggleButton) and w.get_tooltip_text() == "Center"]
        tb[0].set_active(True)
        ital = [w for w in ws if isinstance(w, Gtk.ToggleButton) and w.get_tooltip_text() == "Italic"][0]
        ital.set_active(True)
        GLib.timeout_add(600, lambda: (shot("modify"), dlg.response(Gtk.ResponseType.OK), False)[2])
        return False
    GLib.timeout_add(800, drive)
    SM.modify_dialog(win, "Heading 1")
def s4():
    h = docapi.para_styles(m()).getByName("Heading 1")
    log("H1", h.CharHeight, h.ParaAdjust, h.CharPosture.value)
    SM.toggle_gallery(win, "Heading 2", False); log("gal", SM.gallery_names(m())[:5])
def s5(): win.engine.connect("state-changed", lambda e,k,v: k==".uno:StateTableCell" and log("cell", repr(v))); SM.select_all(win, "Heading 1"); log("sel", repr(docapi.read_cursor(m()).getString()) if hasattr(docapi.read_cursor(m()),'getString') else "multi")
def s6(): shot("after"); app.quit()
steps(s0, s1, s2, s3, s4, s5, s6, delay=1800)
