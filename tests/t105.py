exec(open("/home/claude/folio2/tests/common.py").read())
from folio import contentcontrols as CC, insertmore as IM, docapi, inspector
A = win.actions; m = lambda: win.engine.model
def s0(): win.unmaximize(); win.resize(1590,960); win.move(0,0); A.insert_text("Agree: "); CC.insert(win, "checkbox")
def s1(): docapi.view_cursor(m()).gotoEnd(False); A.insert_text("  Pick: "); CC.insert(win, "dropdown")
def s2():
    docapi.view_cursor(m()).gotoEnd(False); A.insert_text("  Date: "); CC.insert(win, "date")
def s3():
    log("text", repr(m().getText().getString()))
    # put cursor inside checkbox and simulate click logic
    vc = docapi.view_cursor(m()); vc.gotoStart(False); vc.goRight(8, False)
    cc = CC.control_at_cursor(m()); log("cc", cc is not None and CC.kind_of(cc))
    CC.on_click(win, 100, 100)
def s4():
    log("after", repr(m().getText().getString()))
    vc = docapi.view_cursor(m()); vc.gotoEnd(False); vc.goLeft(3, False)
    cc = CC.control_at_cursor(m()); log("cc2", cc is not None and CC.kind_of(cc))
    docapi.view_cursor(m()).gotoEnd(False); A.insert_text("\n")
    win.engine.sync(lambda: IM.insert_smartart(win, "process"))
def s5():
    from folio import drawing
    g = drawing.selected_shape(m()); log("smart", g and g.Name, IM.is_smartart(m(), g) if g else None)
    win.update_object_tabs()
    log("found", [inspector.inspect(win, k)[0] for k, *_ in inspector.CATEGORIES])
def s6(): shot("cc"); app.quit()
steps(s0, s1, s2, s3, s4, s5, s6, delay=1800)
