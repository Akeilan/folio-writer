import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
def tabs():
    return [(p, k.upper()) for p, k, _l in pv().get("tabs") or []]
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
    check("click sets a center tab at 5.08cm", any(abs(p - 2880) < 45 and al == "CENTER" for p, al in tabs()), tabs())
    shot("r8_tab")
    # drag it 1cm right
    X("mousemove", sx, sy); X("mousedown", 1)
    dx = 1000 * g["k"]
    for i in range(1, 6): X("mousemove", int(sx + dx * i / 5), sy); time.sleep(0.05)
    X("mouseup", 1); yield 0.8
    check("dragging moves the tab", any(abs(p - 3447) < 68 for p, al in tabs()) and not any(abs(p - 2880) < 34 for p, al in tabs()), tabs())
    # drag off the ruler
    nx = int(sx + dx)
    X("mousemove", nx, sy); X("mousedown", 1)
    for i in range(1, 6): X("mousemove", nx, sy + 12 * i); time.sleep(0.05)
    X("mouseup", 1); yield 0.8
    check("dragging off removes the tab", not tabs(), tabs())
    # margin drag
    left0 = page_setup()["left"]
    g = hr.geometry(hr.page_box())
    mx, my = screen_of_widget(hr, g["mleft"], a.height / 2)
    X("mousemove", mx, my); X("mousedown", 1)
    for i in range(1, 6): X("mousemove", int(mx + 1000 * g["k"] * i / 5), my); time.sleep(0.05)
    X("mouseup", 1); yield 1.0
    left1 = page_setup()["left"]
    check("dragging the margin edge changes the left margin", abs(left1 - left0 - 567) < 113, (left0, left1))
    vr = win.rulers.v
    e = vr._edges()
    if e:
        vx, vy = screen_of_widget(vr, vr.get_allocation().width / 2, e[0])
        top0 = page_setup()["top"]
        X("mousemove", vx, vy); X("mousedown", 1)
        for i in range(1, 6): X("mousemove", vx, int(vy + 500 * e[3] * i / 5)); time.sleep(0.05)
        X("mouseup", 1); yield 1.0
        top1 = page_setup()["top"]
        check("dragging the top margin on the vertical ruler", abs(top1 - top0 - 283) < 85, (top0, top1))
    shot("r8_after")
    # double-click opens Tabs dialog
    X("mousemove", int(screen_of_widget(hr, hr.geometry(hr.page_box())["mleft"] + 8000 * g["k"], a.height - 5)[0]), sy)
    X("click", "--repeat", 2, "--delay", 80, 1); yield 1.2
    check("double-click ruler opens Tabs", bool(dlg("Tab")), [x.get_title() for x in dialogs_open()])
    close_dialogs(); yield 0.4
run_scenarios(d)
