exec(open("/home/claude/folio2/tests/common.py").read())
from folio import docapi, bridge
e = win.engine; m = lambda: e.model
st = {}
def s0():
    win.actions.apply_style("Heading 1"); win.actions.insert_text("A heading"); e.command(".uno:InsertPara"); win.actions.apply_style("Normal")
    for i in range(10): win.actions.insert_text("Filler line %d. " % i * 6); e.command(".uno:InsertPara")
    win.actions.insert_text("Picture para. "); docapi.insert_picture(m(), "/tmp/pic.png")
def s1():
    g = m().getGraphicObjects().getByIndex(0); st["g"] = g
    vc = docapi.view_cursor(m()); vc.gotoRange(g.getAnchor().getStart(), False)
    log("anchor para pos", vc.getPosition().X, vc.getPosition().Y)
    for anchor in ("AS_CHARACTER", "AT_PARAGRAPH"):
        st.setdefault("res", [])
    g.AnchorType = bridge.enum("com.sun.star.text.TextContentAnchorType", "AT_PARAGRAPH")
def s2():
    g = st["g"]; docapi.select_object(m(), g)
def s3():
    g = st["g"]
    log("state pos", e.state.get(".uno:Position"), "size", e.state.get(".uno:Size"))
    log("VertOrient", g.VertOrient, g.VertOrientPosition, g.VertOrientRelation, "Hori", g.HoriOrient, g.HoriOrientPosition, g.HoriOrientRelation)
    log("pages", e.page_rects()[:1], "setup", docapi.page_setup(m()))
    vc = docapi.view_cursor(m()); vc.gotoRange(g.getAnchor().getStart(), False); p = vc.getPosition()
    cur = g.getAnchor().getText().createTextCursorByRange(g.getAnchor().getStart())
    log("para caret", p.X, p.Y, "ptop", cur.ParaTopMargin, "pbot", cur.ParaBottomMargin, "ls", cur.ParaLineSpacing.Mode, cur.ParaLineSpacing.Height, "h", cur.CharHeight)
    r = e.page_rects()[0]
    surf = e.render(r[0], r[1], r[2], 8000, 1000); surf.write_to_png("/tmp/t143.png")
    app.quit()
steps(s0, s1, s2, s3, delay=2000)
