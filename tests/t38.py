exec(open("/home/claude/folio2/tests/common.py").read())
A = win.actions
def s0(): A.insert_text("First line here."); A.cmd(".uno:InsertPara"); A.insert_text("Second line.")
def s1():
    r = win.engine.page_rects()[0]
    # top-left of text area: page x + 1440 margin, y + 1440
    tx, ty = r[0] + 1440 + 10, r[1] + 1440 + 100
    px, py = win.engine.twips_to_px(tx, ty)
    win.drop._picture("/tmp/drop.png", px, py)
def s2():
    t = win.engine.model.getText()
    log("graphics", win.engine.model.getGraphicObjects().getCount())
    g = win.engine.model.getGraphicObjects().getByIndex(0)
    log("anchor para", repr(g.getAnchor().getText().createTextCursorByRange(g.getAnchor()).getStart() and ""), "first para?",
        t.compareRegionStarts(g.getAnchor(), t.getStart()))
    shot("drop"); app.quit()
steps(s0, s1, s2, delay=2500)
