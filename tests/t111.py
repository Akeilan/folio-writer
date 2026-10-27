exec(open("/home/claude/folio2/tests/common.py").read())
A = win.actions
adj = win.canvas.get_vadjustment()
def s0():
    for i in range(60):
        A.insert_text("Paragraph %d with some text. " % i * 4)
        win.engine.command(".uno:InsertPara")
def s1():
    adj.set_value(2000); pump(0.3)
    log("before", adj.get_value())
    win.ribbon.get_toplevel().get_focus()
    # move focus away then back
    e = Gtk.Entry(); 
    log("vp focus adj", win.canvas.get_child().get_focus_vadjustment(), win.canvas.get_focus_vadjustment())
    w = win.status if hasattr(win, "status") else None
    win.engine.view.get_toplevel().set_focus(None); pump(0.2)
    win.focus_document(); pump(0.3)
    log("after refocus", adj.get_value())
    win.engine.view.grab_focus()
    subprocess.run(["xdotool", "key", "ctrl+End"]); pump(1)
    log("ctrl+end", adj.get_value(), adj.get_upper()); shot("t111a")
    for i in range(25):
        subprocess.run(["xdotool", "key", "Up"]); pump(0.05)
    pump(0.5); log("after ups", adj.get_value()); shot("t111b")
    subprocess.run(["xdotool", "key", "ctrl+Home"]); pump(1)
    log("ctrl+home", adj.get_value()); app.quit()
steps(s0, s1, delay=3000)
