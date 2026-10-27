exec(open("/home/claude/folio2/tests/common.py").read())
A = win.actions; m = lambda: win.engine.model
def s0(): win.unmaximize(); win.resize(1590,960); win.move(0,0); A.insert_text("Some text to annotate with ink strokes on the page.")
def s1(): win.select_tab("Draw"); win.ink.begin("pen2")
def s2():
    pts = [(500 + i*6, 330 + 15*__import__('math').sin(i/3)) for i in range(40)]
    win.ink._create("pen2", pts); win.ink._create("highlighter", [(500, 300), (700, 300)])
def s3():
    dp = m().getDrawPage()
    for i in range(dp.getCount()):
        sh = dp.getByIndex(i); log(sh.Name, sh.Position.X, sh.Position.Y, sh.Size.Width, sh.Size.Height, sh.AnchorPageNo, sh.HoriOrientPosition, sh.VertOrientPosition, [ (p.X,p.Y) for p in sh.PolyPolygon[0]][:3], sh.LineWidth)
    log("shapes", m().getDrawPage().getCount()); shot("ink"); return
def s3b(): win.ink.begin("eraser"); win.ink._erase_at(600, 300)
def s4(): log("after erase", m().getDrawPage().getCount()); win.ink.stop(); shot("ink2"); app.quit()
steps(s0, s1, s2, s3, s3b, s4, delay=2000)
