import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
def a():
    win.open_file("/tmp/wfid/fid.docx"); yield 4.0
    note("comments", [c["text"] for c in comments()])
    caret_end(); yield 1.0
    note("status page label", [w.get_label() for w in find_widget(win.status, lambda w: isinstance(w, Gtk.Button) and "Page" in (w.get_label() or ""))])
def b():
    fresh(); yield 0.4
    T("The happy dog"); yield 0.5
    find("happy").select(); yield 0.4
    K("shift+F7"); yield 2.0
    shot("w4c_thes")
run_scenarios(a, b)
