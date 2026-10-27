exec(open("/home/claude/folio2/tests/common.py").read())
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
