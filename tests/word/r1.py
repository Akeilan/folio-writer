import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
def word_xy(word, frac, nth=0):
    r = find(word, nth); r.caret_to_start(); yield 0.3
    x0, y0, w, h = win._follow_rect
    r.caret_to_end(); yield 0.3
    x1 = win._follow_rect[0]
    P["xy"] = doc_screen(x0 + (x1 - x0) * frac, y0 + h / 2)
P = {}
def homeend():
    fresh(); yield 0.3
    T("one two three"); K("Return"); T("second para"); yield 0.5
    K("Home"); yield 0.3; check("Home", pos() == "", repr(pos()))
    K("End"); yield 0.3; check("End", pos().lower() == "second para", repr(pos()))
    K("shift+Home"); yield 0.3; check("Shift+Home", (sel() or "").lower() == "second para", repr(sel()))
    K("ctrl+Home"); yield 0.3; K("End"); yield 0.3; check("End line 1", pos() == "One two three", repr(pos()))
    K("Home"); K("shift+End"); yield 0.3; check("Shift+End", sel() == "One two three", repr(sel()))
    K("ctrl+End"); yield 0.3; check("Ctrl+End still", pos().lower() == "second para", repr(pos()))
def mouse():
    fresh(); yield 0.3
    win.actions.insert_text("Alpha bravo charlie. Delta echo foxtrot golf.")
    E.command(".uno:InsertPara"); win.actions.insert_text("Second paragraph here.")
    yield 0.8
    yield from word_xy("echo", 0.5)
    click(*P["xy"]); yield 0.6
    X("click", "--repeat", 3, "--delay", 90, 1); yield 1.0
    check("triple-click selects paragraph", (sel() or "").startswith("Alpha bravo") and "golf." in (sel() or ""), repr(sel()))
    click(*P["xy"]); yield 0.6
    click(*P["xy"], mods="ctrl"); yield 1.0
    check("ctrl+click selects sentence", (sel() or "").strip() == "Delta echo foxtrot golf.", repr(sel()))
    # drag-and-drop move
    find("bravo ").select(); yield 0.6
    yield from word_xy("bravo", 0.5)
    s = P["xy"]
    yield from word_xy("here", 0.0)
    d = P["xy"]
    find("bravo ").select(); yield 0.8
    X("mousemove", *s); time.sleep(0.1); X("mousedown", 1); time.sleep(0.2)
    for i in range(1, 12):
        X("mousemove", int(s[0] + (d[0] - s[0]) * i / 11), int(s[1] + (d[1] - s[1]) * i / 11)); time.sleep(0.05)
    X("mouseup", 1); yield 1.2
    check("drag-and-drop moves text", para_texts() == ["Alpha charlie. Delta echo foxtrot golf.", "Second paragraph bravo here."], para_texts())
    K("ctrl+z"); yield 0.8
    check("undo restores (one step)", para_texts()[0].startswith("Alpha bravo"), para_texts())
    # click inside selection just places caret
    find("Delta echo").select(); yield 0.6
    yield from word_xy("echo", 0.5)
    find("Delta echo").select(); yield 0.6
    click(*P["xy"]); yield 0.8
    check("click inside selection collapses it", not sel(), repr(sel()))
    # ordinary drag-select still works
    yield from word_xy("Second", 0.0); a = P["xy"]
    yield from word_xy("paragraph", 1.0); b = P["xy"]
    X("mousemove", *a); X("mousedown", 1)
    for i in range(1, 8): X("mousemove", int(a[0] + (b[0] - a[0]) * i / 7), a[1]); time.sleep(0.05)
    X("mouseup", 1); yield 0.8
    check("drag-select still works", sel() == "Second paragraph", repr(sel()))
run_scenarios(homeend, mouse)
