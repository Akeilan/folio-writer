exec(open("/home/claude/folio2/tests/common.py").read())
from folio import drawing, arrange, docapi, bridge
m = lambda: win.engine.model
def s0():
    win.actions.insert_text("x")
    drawing.insert_shape(m(), "rectangle", 1, 3000, 4000, 4000, 3000)
    drawing.insert_shape(m(), "ellipse", 1, 5000, 5000, 4000, 3000)
def s1():
    arrange.select(m(), arrange.all_objects(m())); log("sel", len(arrange.selected_objects(m())))
    win.engine.command(".uno:Merge")
def s2():
    log("after merge", [o.getShapeType() for o in arrange.all_objects(m())])
    # fontwork
    sh = m().createInstance("com.sun.star.drawing.CustomShape")
    sh.Size = bridge.struct("com.sun.star.awt.Size", Width=8000, Height=3000)
    sh.AnchorType = bridge.enum("com.sun.star.text.TextContentAnchorType", "AT_PAGE")
    m().getDrawPage().add(sh)
    drawing._anchor_page(sh, 1, 3000, 12000)
    import uno
    tp = (bridge.prop("TextPath", True), bridge.prop("ScaleX", False))
    geo = (bridge.prop("Type", "fontwork-arch-up-curve"), bridge.prop("TextPath", uno.Any("[]com.sun.star.beans.PropertyValue", tp)))
    uno.invoke(sh, "setPropertyValue", ("CustomShapeGeometry", uno.Any("[]com.sun.star.beans.PropertyValue", geo)))
    sh.setString("Arched Text")
    sh.FillColor = 0x4472C4; sh.LineStyle = bridge.enum("com.sun.star.drawing.LineStyle","NONE")
def s3(): shot("merge_fw"); app.quit()
steps(s0, s1, s2, s3, delay=1800)
