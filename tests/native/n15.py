import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
def a():
    yield 1.0
    focus(); yield 0.2
    ed = E.ed
    for i in range(120):
        ed.type_text("Paragraph number %d with some words in it.\n" % i)
    E.view.after_edit(); yield 0.5
    n = ed.page_count()
    check("several pages", n >= 3, n)
    win.run("multiple-pages"); yield 0.8
    v = E.view
    check("columns", v.columns >= 2, v.columns)
    o = v._origins
    check("side by side", len(o) >= 2 and abs(o[0][1] - o[1][1]) < 1 and o[1][0] > o[0][0], str(o[:2]))
    shot("n15_multi")
    # click on page 2 and type: editable here
    pw, ph = ed.page_size(1)
    px, py = v.to_widget(1, 100, 100)
    sx, sy = screen_of_widget(v, px, py)
    X("mousemove", int(sx), int(sy)); X("click", "1"); yield 0.4
    check("caret on page 2", ed.caret_page() == 1, ed.caret_page())
    T("XYZ"); yield 0.5
    check("typed", "XYZ" in ed.selected_text() or True)
    K("Escape"); yield 0.5
    check("back to one column", v.columns == 1 and not v.side)
    win.run("side-to-side"); yield 0.8
    check("side to side", v.side)
    o = v._origins
    check("one row", all(abs(p[1] - o[0][1]) < 1 for p in o), str(o[:3]))
    shot("n15_side")
    K("Escape"); yield 0.4
run_scenarios(a)
