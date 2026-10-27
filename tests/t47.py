exec(open("/home/claude/folio2/tests/common.py").read())
from folio import docapi
m = lambda: win.engine.model
def s0(): win.actions.insert_text("x ")
def s1(): win.eqbar.new_equation("a+b"); 
def s2(): win.eqbar.finish()
def s3():
    f = docapi.formulas(m())[0]; c = m().getCurrentController(); log("sel ok", c.select(f))
    log("sel", c.getSelection().getImplementationName(), win.engine.selection_type())
    fr = m().getTextFrames(); log("frames", fr.getCount())
    app.quit()
steps(s0, s1, s2, s3, delay=2000)
