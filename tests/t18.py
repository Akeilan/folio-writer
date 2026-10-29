import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
def closer():
    for w in Gtk.Window.list_toplevels():
        if isinstance(w, Gtk.Dialog) and w.get_visible():
            log("closing", w.get_title()); w.response(Gtk.ResponseType.CANCEL)
    return True
GLib.timeout_add(1500, closer)
def s0(): win.actions.insert_text("Hello"); log("a")
def s1(): log("fonts", len(win.engine.fonts()))
def s2(): log("open font dialog"); win.dialogs.font_dialog(); log("closed font dialog")
def s3(): log("para"); win.dialogs.paragraph_dialog(); log("closed para")
def s4(): log("done"); app.quit()
steps(s0, s1, s2, s3, s4, delay=2000)
