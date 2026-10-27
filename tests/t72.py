exec(open("/home/claude/folio2/tests/common.py").read())
from folio import insertextras as IX, docapi
A = win.actions; m = lambda: win.engine.model
def s0(): win.unmaximize(); win.resize(1590,960); win.move(0,0); A.insert_text("Intro text.")
def s1(): IX.insert_wordart(m(), 1, "Hello WordArt")
def s2(): docapi.view_cursor(m()).gotoEnd(False); IX.insert_signature_line(m(), "Ron S.", "Engineer", "", True)
def s3(): IX.insert_textbox(m(), "sidebar")
def s4(): IX.insert_textbox(m(), "quote")
def s5(): win.select_tab("Insert"); shot("extras"); log(repr(m().getText().getString())); app.quit()
steps(s0, s1, s2, s3, s4, s5, delay=2000)
