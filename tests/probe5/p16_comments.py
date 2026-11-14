import os as _o; TESTS = _o.environ["FOLIO_WRITER_TESTS"]; exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read()); exec(open("/tmp/p5/probes/ph.py").read())
def a():
    yield 1.0
    focus(); fresh(); yield 0.3
    T("First paragraph of text here.\nSecond paragraph with a remark on it.\nThird paragraph."); yield 0.3
    find("remark").select(); yield 0.3
    note("markup/balloons before", (ed().markup(), ed().balloons()))
    K("ctrl+alt+m"); yield 1.0
    shot("c_new")
    note("focus after New Comment", (type(win.get_focus()).__name__, [d.get_title() for d in dialogs_open()], ed().story()))
    T("This is my comment"); yield 0.5
    shot("c_typed")
    note("comments", comment_texts())
    note("body after typing", text())
    check("typing after New Comment goes into the comment, not the page", "This is my comment" not in text(), text()[:120])
    check("the comment holds what was typed", any("This is my comment" in c for c in comment_texts()), comment_texts())
    K("Escape"); yield 0.4
    win.save_to("/tmp/p5out/c1.docx"); yield 0.5
    win.open_file("/tmp/p5out/c1.docx"); yield 2.0
    shot("c_reopened")
    note("after reopen", (comment_texts(), ed().markup(), ed().balloons()))
run_scenarios(a)
