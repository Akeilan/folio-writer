import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
from folio import stylemodify as SM, docapi
A = win.actions; m = lambda: win.engine.model
def closer(after):
    def go():
        ds = [w for w in Gtk.Window.list_toplevels() if isinstance(w, Gtk.Dialog) and w.get_visible()]
        if ds: after(ds)
        return False
    return go
def s0(): A.insert_text("Some text")
def s1():
    # Format > Font on Title style through proxy
    st = docapi.para_styles(m()).getByName("Title"); px = SM.StyleProxy(st)
    win.dialogs._style_target = px
    GLib.timeout_add(900, closer(lambda ds: ds[-1].response(Gtk.ResponseType.OK)))
    win.dialogs.font_dialog(); win.dialogs._style_target = None
    log("font proxy pending", sorted(px.pending), "doc text intact", repr(m().getText().getString()))
def s2():
    def fill(ds):
        d = ds[-1]
        def walk(w, out):
            out.append(w)
            if isinstance(w, Gtk.Container):
                for c in w.get_children(): walk(c, out)
            return out
        e = [w for w in walk(d, []) if isinstance(w, Gtk.Entry)]
        e[0].set_text("My Style"); e[2].set_text("15")
        d.response(Gtk.ResponseType.OK)
    GLib.timeout_add(900, closer(fill))
    SM.modify_dialog(win, None)
    s = docapi.para_styles(m()).getByName("My Style")
    log("new", s.CharHeight, docapi.read_cursor(m()).ParaStyleName, SM.gallery_names(m())[-1])
def s3():
    app.settings["style_keys"] = {"ctrl+alt+9": "Heading 2"}; win.keymap.set_style_keys(app.settings["style_keys"])
    import subprocess; subprocess.run(["xdotool","key","ctrl+alt+9"])
def s4(): log("after key", docapi.read_cursor(m()).ParaStyleName); app.settings["style_keys"] = {}; app.quit()
steps(s0, s1, s2, s3, s4, delay=2000)
