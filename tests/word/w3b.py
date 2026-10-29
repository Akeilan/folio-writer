import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
def redlines():
    return [(c[0], c[1]) for c in changes()]
def a():
    fresh(); yield 0.3
    win.actions.cmd(".uno:InsertTable", {"Columns": 2, "Rows": 2}); yield 0.8
    rib("Table Layout", "Select", "Select Table"); yield 0.6
    note("sel after Select Table", repr(sel()))
    K("BackSpace"); yield 0.6
    check("Select Table + Backspace deletes table", len(tables()) == 0, len(tables()))
    if len(tables()):
        rib("Table Layout", "Select", "Select Table"); yield 0.6
        K("Delete"); yield 0.6
        note("Delete key on selected table", len(tables()))
def b():
    fresh(); yield 0.3
    for i, h in enumerate(("Intro", "Methods", "Results")):
        T(h); K("ctrl+alt+1"); K("Return"); T("Body text %d." % i); K("Return"); yield 0.3
    K("ctrl+Home"); yield 0.3
    rib("References", "Table of Contents", "Automatic Table 1"); yield 1.5
    check("insert TOC", len(tocs()) == 1, len(tocs()))
    shot("w3b_toc")
    if tocs():
        note("toc", repr(tocs()[0]))
        type_at(find_all("Results")[-1], "Findings"); yield 0.3
        rib("References", "Update Table"); yield 1.5
        note("update dialog", [d.get_title() for d in dialogs_open()])
        respond("Update", Gtk.ResponseType.OK); yield 1.0
        s = tocs()[0]
        check("Update Table refreshes TOC", "Findings" in s, repr(s))
        # ctrl+click TOC entry jumps
def c():
    fresh(); yield 0.3
    T("Original sentence here."); yield 0.4
    K("ctrl+shift+e"); yield 0.5
    K("ctrl+Home"); T("New "); yield 0.5
    note("redlines after insert", redlines())
    K("ctrl+End"); yield 0.3; K("BackSpace"); yield 0.5
    note("redlines after backspace", redlines())
    find("sentence").select(); yield 0.3
    K("ctrl+b"); yield 0.5
    note("redlines after bold", redlines())
    shot("w3b_track")
    K("ctrl+shift+e"); yield 0.3
def d():
    fresh(); yield 0.3
    rib("Layout", "Margins", "Narrow"); yield 0.6
    check("Margins Narrow", abs(page_setup()["left"] - 720) < 12, page_setup()["left"])
    rib("Design", "Watermark", "CONFIDENTIAL"); yield 1.0
    shot("w3b_wm")
    T("Hello"); yield 0.6
    find("Hello").select(); yield 0.3
    K("shift+F7"); yield 1.2
    shot("w3b_thes")
    note("after shift+F7", [d.get_title() for d in dialogs_open()])
    close_dialogs(); yield 0.3
    rib("Insert", "Page Number"); yield 1.0
    shot("w3b_pagenum")
    K("Escape"); yield 0.3
run_scenarios(a, b, c, d)
