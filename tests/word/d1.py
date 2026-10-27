exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
def a():
    fresh(); yield 0.3
    T("Once upon a time there was a long paragraph that keeps going and going so that it wraps across several lines of text in the document body here. " * 3); yield 0.5
    K("ctrl+Home"); yield 0.3
    docapi.drop_cap(M(), "drop", 3, 0); yield 0.5
    K("ctrl+End"); T("\nSecond paragraph."); yield 0.3
    note("before", [(p.getString()[:10], p.DropCapFormat.Lines) for p in paras()])
    ok = win.save_to("/tmp/dc/dc.docx"); yield 3.0
    note("saved", ok)
    import zipfile
    x = zipfile.ZipFile("/tmp/dc/dc.docx").read("word/document.xml").decode()
    note("xml", x[x.find("<w:body>"):][:900])
    win.open_file("/tmp/dc/dc.docx"); yield 5.0
    dc = [(p.getString()[:10], p.DropCapFormat.Lines) for p in paras() if p.supportsService("com.sun.star.text.Paragraph")]
    note("reopened", dc)
    note("frames", M().getTextFrames().getElementNames())
    check("drop cap survives docx", any(l == 3 for s, l in dc), dc)
run_scenarios(a)
