import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
from folio import docapi, drawing
A = win.actions
m = lambda: win.engine.model
def s0(): win.unmaximize(); win.resize(1590,960); win.move(0,0); A.insert_text("Text before picture. ")
def s1(): docapi.insert_picture(m(), "/tmp/pic.png"); win.update_object_tabs()
def s2():
    log("sel", drawing.selected_shape(m()), win.engine.selection_type())
    log("tab", win.ribbon.current.name if win.ribbon.current else None, "spins", [sb.get_value() for sb in win.obj_spins["width"]])
    win.ribbon.select([t for t in win.ribbon.tabs if t.name=="Picture Format"][0])
def s3(): shot("pic0"); win.object_call("set_picture_style", "Simple Frame, White")
def s4(): win.object_call("set_adjust", 20, 20); win.object_call("set_color_mode", "grayscale")
def s5(): win.object_call("crop_to_ratio", 1, 1)
def s6():
    o = drawing.selected_shape(m()); log("size", drawing.size_of(o), "crop", o.GraphicCrop.Left, o.GraphicCrop.Right)
    win.object_call("rotate", "right"); win.run("alt-text")
def s7():
    from folio.panes import AltTextPane
    p = win.panes[AltTextPane]; p.view.get_buffer().set_text("A gradient with a circle")
    o = drawing.selected_shape(m()); log("alt", o.Description, "rot", o.GraphicRotation)
    win.obj_spins["width"][0].set_value(3000)
def s8():
    o = drawing.selected_shape(m()); log("size after width", drawing.size_of(o)); shot("pic1")
    win.object_call("reset_picture", True)
def s9():
    o = drawing.selected_shape(m()); log("reset", o.GraphicRotation, o.GraphicCrop.Left, o.AdjustLuminance); shot("pic2"); app.quit()
steps(s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, delay=2000)
