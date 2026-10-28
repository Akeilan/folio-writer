exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
def a():
    fresh(); yield 0.3
    T("Once upon a time there was a long paragraph that keeps going and going so that it wraps across several lines of text in the document body here. " * 3); yield 0.5
    K("ctrl+Home"); yield 0.3
    E.ed.set_drop_cap("drop", 3, 0, None); E.view.after_edit(); yield 0.5
    K("ctrl+End"); T("\nSecond paragraph."); yield 0.3
    check("drop cap set", bool(drop_caps()) and drop_caps()[0][1][1] == 3, drop_caps())
    ok = win.save_to("/tmp/dc/dc.docx"); yield 3.0
    note("saved", ok)
    import zipfile
    x = zipfile.ZipFile("/tmp/dc/dc.docx").read("word/document.xml").decode()
    note("xml", x[x.find("<w:body>"):][:900])
    win.open_file("/tmp/dc/dc.docx"); yield 5.0
    dc = drop_caps()
    note("reopened", dc)
    check("drop cap survives docx", any(i[0] == "drop" and i[1] == 3 for _t, i in dc), dc)
run_scenarios(a)
