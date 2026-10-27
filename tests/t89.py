exec(open("/home/claude/folio2/tests/common.py").read())
from folio import docapi, drawing
A = win.actions; m = lambda: win.engine.model
st = {}
def ev(t, x, y, mods=0):
    doc = win.engine._doc_ptr(); doc.contents.pClass.contents.postMouseEvent(doc, t, int(x), int(y), 1, 1 if t != 1 else 1, mods)
def s0(): A.insert_text("Text before. More text here to drop into."); docapi.insert_picture(m(), "/tmp/pic.png")
def s1():
    win.update_object_tabs(); o = drawing.selected_shape(m()); st['o']=o
    log("before", o.Size.Width, o.Size.Height, win.engine.state.get(".uno:Position"), win.engine.state.get(".uno:Size"))
    r = win.layout_options.rect; log("rect", r)
    x,y,w,h = r; z = win.engine.view.get_zoom()
    tx, ty = (x+w)*15/z, (y+h/2)*15/z
    ev(0, tx, ty)
    for i in range(1,6): ev(2, tx - i*300, ty)
    ev(1, tx-1500, ty)
def s2():
    o = drawing.selected_shape(m()); log("after native resize", o and (o.Size.Width, o.Size.Height), win.engine.state.get(".uno:Size"))
    win.update_object_tabs()
def s2b():
    win.object_call("set_wrap", "square")
    o = m().getGraphicObjects().getByIndex(0); docapi.controller(m()).select(o); st['o']=o
def s2c(): win.update_object_tabs(); log("pos0", st['o'].HoriOrientPosition, st['o'].VertOrientPosition, st['o'].AnchorType.value)
def s3():
    log("rect2", win.layout_options.rect)
    x,y,w,h = win.layout_options.rect; z = win.engine.view.get_zoom()
    cx, cy = (x+w/2)*15/z, (y+h/2)*15/z
    ev(0, cx, cy)
    for i in range(1,6): ev(2, cx + i*400, cy - i*800)
    ev(1, cx+2000, cy-4000)
def s4(): o = drawing.selected_shape(m()); log("pos", o and (o.HoriOrientPosition, o.VertOrientPosition, o.AnchorType.value)); log("text", repr(m().getText().getString())); shot("native"); app.quit()
steps(s0, s1, s2, s2b, s2c, s3, s4, delay=1800)
