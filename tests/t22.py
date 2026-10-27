exec(open("/home/claude/folio2/tests/common.py").read())
tabs = ["Home", "Insert", "Design", "Layout", "References", "Review", "View", "Help"]
fns = [lambda: (win.unmaximize(), win.resize(1590, 960), win.move(0,0))]
for t in tabs:
    fns.append(lambda t=t: win.ribbon.select(win.ribbon.tab_by_name(t)))
    fns.append(lambda t=t: shot("tab_" + t))
fns.append(lambda: app.quit())
steps(*fns, delay=1000)
