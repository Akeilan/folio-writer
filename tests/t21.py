exec(open("/home/claude/folio2/tests/common.py").read())
def s0(): win.unmaximize(); win.resize(1590, 960); win.move(0,0)
def s1(): win.actions.insert_text("Wide window test."); 
def s2(): shot("w_home")
def s3(): win.ribbon.select(win.ribbon.tab_by_name("Insert"))
def s4(): shot("w_insert"); win.resize(980, 760)
def s5(): win.ribbon.select(win.ribbon.tab_by_name("Home"))
def s6(): shot("n_home"); win.ribbon.select(win.ribbon.tab_by_name("Insert"))
def s7(): shot("n_insert")
def s8():
    g = [g for g in win.ribbon.current.groups if g.collapsed]
    log("collapsed", [x.caption for x in g])
    if g: g[0].open_compact()
def s9(): shot("n_popup"); app.quit()
steps(s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, delay=1500)
