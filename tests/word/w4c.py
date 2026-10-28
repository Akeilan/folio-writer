exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
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
