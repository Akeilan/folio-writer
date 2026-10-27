exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
HELPER = "/home/claude/folio2/tests/word/helpers/ext_src.py"
EV = []
for w, nm in ((E.view, "view"), (win, "win")):
    w.connect("drag-motion", lambda *a, nm=nm: EV.append(nm + ":motion") and False)
    w.connect("drag-drop", lambda *a, nm=nm: EV.append(nm + ":drop") and False)
    w.connect("drag-data-received", lambda *a, nm=nm: EV.append(nm + ":recv") and False)
def d_drag():
    fresh(); yield 0.3
    T("Drop here: "); yield 0.4
    p = subprocess.Popen(["/usr/bin/python3", HELPER, "text"], env=dict(os.environ, DISPLAY=os.environ.get("DISPLAY", ":99")))
    yield 2.0
    c = vc(); x0, y0, w, h = win._follow_rect
    dx, dy = doc_screen(x0 + 200, y0 + h / 2)
    sx, sy = 1320 + 100, 120 + 50
    X("mousemove", sx, sy); time.sleep(0.3); X("mousedown", 1); time.sleep(0.3)
    for i in range(1, 30):
        X("mousemove", int(sx + (dx - sx) * i / 29), int(sy + (dy - sy) * i / 29)); time.sleep(0.05)
        yield 0.02
    yield 0.5
    X("mouseup", 1); yield 2.0
    note("events", sorted(set(EV)))
    note("text", repr(text()))
    shot("c2")
    p.kill()
run_scenarios(d_drag)
