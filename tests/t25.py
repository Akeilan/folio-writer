import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
def s0(): win.unmaximize(); win.resize(1590, 960); win.move(0,0); win.actions.insert_text("Some text here.")
def s1(): win.ribbon.select([t for t in win.ribbon.tabs if t.name=="References"][0])
def s2(): shot("refs"); GLib.timeout_add(300, lambda: win.run_window_action("language-dialog"))
def s3(): shot("lang")
def s4():
    for w in Gtk.Window.list_toplevels():
        if isinstance(w, Gtk.Dialog) and w.get_visible(): w.response(Gtk.ResponseType.CANCEL)
    win.run_window_action("mark-entry")
def s5(): shot("mark"); app.quit()
steps(s0, s1, s2, s3, s4, s5, delay=1800)
