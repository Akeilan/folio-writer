exec(open("/home/claude/folio2/tests/common.py").read())
A = win.actions; m = lambda: win.engine.model
def s0(): win.unmaximize(); win.resize(1590,960); win.move(0,0); A.insert_text("Body text here. "*30)
def s1(): win.run("header")
def s2(): A.insert_text("My header"); win.update_object_tabs()
def s3(): shot("hfedit")
def s4(): win.run("close-header-footer") if hasattr(win,'act_close_header_footer') else win.engine.command(".uno:CloseHeaderFooter") 
def s5():
    from folio import docapi; docapi.view_cursor(m()).gotoRange(m().getText().getEnd(), False); win.update_object_tabs()
def s6(): shot("hfbody"); app.quit()
steps(s0, s1, s2, s3, s4, s5, s6, delay=1800)
