exec(open("/home/claude/folio2/tests/common.py").read())
def s0():
    win.ribbon.display_options(win.ribbon.collapse_btn)
def s1():
    shot("t147a")
    for w in Gtk.Window.list_toplevels():
        pass
    win.ribbon.set_display_mode("full")
def s2():
    shot("t147b"); win.peek_ribbon(True)
def s3():
    shot("t147c"); win.ribbon.set_display_mode("tabs")
def s4():
    shot("t147d"); win.ribbon.set_display_mode("always")
def s5():
    shot("t147e"); log("mode", app.settings.get("ribbon_mode")); app.quit()
steps(s0, s1, s2, s3, s4, s5, delay=1200)
