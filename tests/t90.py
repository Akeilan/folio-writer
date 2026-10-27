exec(open("/home/claude/folio2/tests/common.py").read())
from folio import docapi, accessibility, drawing
m = lambda: win.engine.model
def s0(): win.actions.insert_text("x "); docapi.insert_picture(m(), "/tmp/pic.png"); win.eqbar.new_equation("x^2")
def s1():
    win.eqbar.finish(); g=m().getGraphicObjects(); log("n", g.getCount(), [(g.getByIndex(i).Name, g.getByIndex(i).Title, g.getByIndex(i).Description) for i in range(g.getCount())]); log([(c,l) for c,l,t in accessibility.check(m())]); app.quit()
steps(s0, s1, delay=1800)
