exec(open("/home/claude/folio2/tests/common.py").read())
from folio import drawing, docapi, bridge
A = win.actions; m = lambda: win.engine.model
def s0(): A.insert_text("x"); drawing.insert_shape(m(), "pentagon", 1, 3000, 4000, 4000, 3000)
def s1():
    o = drawing.selected_shape(m())
    import uno
    e = bridge.create("com.sun.star.drawing.EnhancedCustomShapeEngine", bridge.prop("CustomShape", o))
    try:
        x = e.queryInterface(uno.getTypeByName("com.sun.star.drawing.XCustomShapeEngine"))
        intro = bridge.create("com.sun.star.beans.Introspection")
        ins = intro.inspect(x)
        log("methods", [mm.getName() for mm in ins.getMethods(-1)][:40])
        g = uno.invoke(x, "render", ())
        log("type", g.getShapeType(), hasattr(g, "getCount") and g.getCount())
        try:
            b = g.PolyPolygonBezier; log("bez", [(p.X,p.Y) for p in b.Coordinates[0]], [str(f.value) for f in b.Flags[0]])
        except Exception as ex: log("nobez", ex)
        try:
            log("pp", [(p.X,p.Y) for p in g.PolyPolygon[0]])
        except Exception as ex: log("nopp", ex)
        log("gpos", g.Position.X, g.Position.Y, g.Size.Width)
    except Exception as ex: log("ex", type(ex), ex)
    dh = bridge.create("com.sun.star.frame.DispatchHelper")
    fr = docapi.controller(m()).getFrame()
    for c in (".uno:ChangeBezier",):
        r = dh.executeDispatch(fr, c, "", 0, ())
        log(c, r.State if r else r)
def s2():
    o = drawing.selected_shape(m()); log("after", o.getShapeType() if o else None)
    app.quit()
steps(s0, s1, s2, delay=1500)
