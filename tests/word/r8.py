exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
def tabs():
    return [(t.Position, t.Alignment.value) for t in (vc().ParaTabStops or ()) if t.Alignment.value != "DEFAULT"]
def d():
    fresh(); yield 0.3
    T("Tabbed\ttext"); yield 0.5
    app.settings["ruler"] = True; win.rulers.set_visible(True); win.rulers.refresh(); yield 0.8
    hr = win.rulers.h
    sel_ = win.rulers.selector
    click(*widget_center(sel_)); yield 0.4
    check("selector cycles to Center Tab", sel_.kind == "CENTER", sel_.kind)
    g = hr.geometry(hr.page_box())
    a = hr.get_allocation()
    x = g["mleft"] + 5080 * g["k"]
    sx, sy = screen_of_widget(hr, x, a.height - 5)
    click(sx, sy); yield 0.8
    check("click sets a center tab at 5.08cm", any(abs(p - 5080) < 80 and al == "CENTER" for p, al in tabs()), tabs())
    shot("r8_tab")
    # drag it 1cm right
    X("mousemove", sx, sy); X("mousedown", 1)
    dx = 1000 * g["k"]
    for i in range(1, 6): X("mousemove", int(sx + dx * i / 5), sy); time.sleep(0.05)
    X("mouseup", 1); yield 0.8
    check("dragging moves the tab", any(abs(p - 6080) < 120 for p, al in tabs()) and not any(abs(p - 5080) < 60 for p, al in tabs()), tabs())
    # drag off the ruler
    nx = int(sx + dx)
    X("mousemove", nx, sy); X("mousedown", 1)
    for i in range(1, 6): X("mousemove", nx, sy + 12 * i); time.sleep(0.05)
    X("mouseup", 1); yield 0.8
    check("dragging off removes the tab", not tabs(), tabs())
    # margin drag
    left0 = docapi.page_setup(M())["left"]
    g = hr.geometry(hr.page_box())
    mx, my = screen_of_widget(hr, g["mleft"], a.height / 2)
    X("mousemove", mx, my); X("mousedown", 1)
    for i in range(1, 6): X("mousemove", int(mx + 1000 * g["k"] * i / 5), my); time.sleep(0.05)
    X("mouseup", 1); yield 1.0
    left1 = docapi.page_setup(M())["left"]
    check("dragging the margin edge changes the left margin", abs(left1 - left0 - 1000) < 200, (left0, left1))
    vr = win.rulers.v
    e = vr._edges()
    if e:
        vx, vy = screen_of_widget(vr, vr.get_allocation().width / 2, e[0])
        top0 = docapi.page_setup(M())["top"]
        X("mousemove", vx, vy); X("mousedown", 1)
        for i in range(1, 6): X("mousemove", vx, int(vy + 500 * e[3] * i / 5)); time.sleep(0.05)
        X("mouseup", 1); yield 1.0
        top1 = docapi.page_setup(M())["top"]
        check("dragging the top margin on the vertical ruler", abs(top1 - top0 - 500) < 150, (top0, top1))
    shot("r8_after")
    # double-click opens Tabs dialog
    X("mousemove", int(screen_of_widget(hr, hr.geometry(hr.page_box())["mleft"] + 8000 * g["k"], a.height - 5)[0]), sy)
    X("click", "--repeat", 2, "--delay", 80, 1); yield 1.2
    check("double-click ruler opens Tabs", bool(dlg("Tab")), [x.get_title() for x in dialogs_open()])
    close_dialogs(); yield 0.4
run_scenarios(d)
