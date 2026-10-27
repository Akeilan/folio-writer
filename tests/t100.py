exec(open("/home/claude/folio2/tests/common.py").read())
from folio import docapi, drawing, arrange, pictools
m = lambda: win.engine.model
st = {}
def s0():
    win.unmaximize(); win.resize(1590,960); win.move(0,0)
    win.actions.insert_text("Pictures ")
    docapi.insert_picture(m(), "/tmp/pic.png")
def s1():
    o = m().getGraphicObjects().getByIndex(0); st['o']=o; docapi.controller(m()).select(o)
    win.update_object_tabs(); win.bg_removal_start()
def s2(): shot("bg"); win.bg_finish(True); win.object_call_module("pictools", "artistic_effect", "Pencil Sketch")
def s3():
    shot("art"); o = st['o']; log("size before", o.Size.Width); pictools.compress(o, 96); log("after", o.Size.Width)
    drawing.insert_shape(m(), "rectangle", 1, 3000, 15000, 4000, 3000)
    drawing.insert_shape(m(), "ellipse", 1, 5000, 16000, 4000, 3000)
def s4():
    objs = [o for o in arrange.all_objects(m()) if o.getShapeType().endswith("CustomShape")]
    made = pictools.merge_shapes(m(), objs, "union"); log("merged", len(made), [o.getShapeType() for o in arrange.all_objects(m())])
def s5(): shot("merged"); app.quit()
steps(s0, s1, s2, s3, s4, s5, delay=2000)
