exec(open("/home/claude/folio2/tests/common.py").read())
A = win.actions
def s0(): win.unmaximize(); win.resize(1590,960); win.move(0,0); A.insert_text("Draft text. "*50)
def s1(): log("draft start"); win.run("draft-view")
def s2(): log("draft on"); shot("draft")
def s3(): win.run("print-layout"); log("back")
def s4(): shot("back"); app.quit()
steps(s0, s1, s2, s3, s4, delay=1800)
