exec(open("/home/claude/folio2/tests/common.py").read())
from folio import docapi, drawing, objecttools
A = win.actions; m = lambda: win.engine.model
def s0(): win.unmaximize(); win.resize(1590,960); win.move(0,0); A.insert_text("Text before picture. ")
def s1(): docapi.insert_picture(m(), "/tmp/pic.png"); win.update_object_tabs()
def s2(): log("rect", objecttools.object_rect(win), "btn", win.layout_options.btn.get_visible()); shot("lo1"); win.layout_options.open()
def s3(): shot("lo2"); [p.popdown() for p in []]; win.crop_mode.begin()
def s4():
    cm = win.crop_mode; x,y,w,h = cm.rect; cm.cut = [w*0.2, 0, 0, h*0.25]; win.engine.view.queue_draw()
def s5(): shot("crop1"); win.crop_mode.apply()
def s6():
    o = drawing.selected_shape(m()); log("after crop", drawing.size_of(o) if o else None, o.GraphicCrop.Left if o else None); shot("crop2"); app.quit()
steps(s0, s1, s2, s3, s4, s5, s6, delay=2000)
