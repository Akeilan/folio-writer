exec(open("/home/claude/folio2/tests/common.py").read())
from folio import drawing, docapi
A = win.actions; m = lambda: win.engine.model
def s0(): win.unmaximize(); win.resize(1590,960); win.move(0,0); A.insert_text("Shapes test.")
def s1(): drawing.insert_shape(m(), "cube", 1, 3000, 4000, 4000, 3000)
def s2():
    win.update_object_tabs(); win.object_call("set_shape_style", 4, 0xED7D31)
def s3(): win.object_call("change_shape", "chevron")
def s4(): drawing.insert_shape(m(), "elbow-connector", 1, 3000, 9000, 5000, 3000)
def s5(): drawing.insert_shape(m(), "curved-connector", 1, 9000, 9000, 4000, 4000)
def s6():
    drawing.insert_shape(m(), "flowchart-decision", 1, 10000, 3000, 3000, 3000)
    win.update_object_tabs()
def s7(): shot("shapes"); win.act_edit_points()
def s8(): shot("editpts"); log("sel", win.engine.selection_type() if hasattr(win.engine,'selection_type') else '')
def s9(): app.quit()
steps(s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, delay=1800)
