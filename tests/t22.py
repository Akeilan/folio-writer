import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
tabs = ["Home", "Insert", "Design", "Layout", "References", "Review", "View", "Help"]
fns = [lambda: (win.unmaximize(), win.resize(1590, 960), win.move(0,0))]
for t in tabs:
    fns.append(lambda t=t: win.ribbon.select(win.ribbon.tab_by_name(t)))
    fns.append(lambda t=t: shot("tab_" + t))
fns.append(lambda: app.quit())
steps(*fns, delay=1000)
