exec(open("/home/claude/folio2/tests/common.py").read())
from folio import insertextras as IX, drawing, docapi
m = lambda: win.engine.model
def s0(): win.unmaximize(); win.resize(1590,960); win.move(0,0); win.actions.insert_text("Intro"); IX.insert_wordart(m(), 1, "Hello WordArt")
def s1(): win.update_object_tabs(); win.wordart_transform("fontwork-arch-up-curve")
def s2():
    o = drawing.selected_shape(m()); log("now", o and o.getShapeType())
    win.wordart_transform("fontwork-wave")
def s3(): shot("transform"); app.quit()
steps(s0, s1, s2, s3, delay=1800)
