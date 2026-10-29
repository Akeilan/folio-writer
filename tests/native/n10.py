import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
def a():
    yield 1.0
    focus(); yield 0.2
    ed = E.ed
    for title, n in (("Overview", 8), ("Design", 40), ("Results", 30)):
        ed.type_text(title)
        win.actions.apply_style("Heading 1")
        ed.type_text("\n")
        win.actions.apply_style("Normal")
        for i in range(n):
            ed.type_text("Body text line %d about %s.\n" % (i, title.lower()))
    E.view.after_edit(); yield 0.5
    ed.move_caret("doc_start", False)
    win.run("insert-toc"); yield 0.6
    texts = [t for t in ed.selected_text().split("\n")] if False else None
    import zipfile
    win.save_to("/tmp/n10a.docx"); yield 0.8
    d = zipfile.ZipFile("/tmp/n10a.docx").read("word/document.xml").decode()
    check("toc field", "TOC \\o" in d and "PAGEREF _Toc" in d)
    check("bookmarks", d.count("w:bookmarkStart") >= 3)
    # a caption and a date field at the end
    ed.move_caret("doc_end", False)
    ed.type_text("\n")
    ed.insert_caption("Figure", "A diagram", True, "ARABIC", False)
    E.view.after_edit(); yield 0.3
    ed.move_caret("doc_end", False)
    ed.type_text("\nPrinted ")
    ed.insert_field_now('DATE \\@ "yyyy-MM-dd"')
    E.view.after_edit(); yield 0.3
    import datetime
    win.save_to("/tmp/n10.docx"); yield 0.8
    d = zipfile.ZipFile("/tmp/n10.docx").read("word/document.xml").decode()
    check("caption", "SEQ Figure" in d and "A diagram" in d)
    check("date", datetime.date.today().isoformat() in d)
    # Alt+F9 shows codes
    K("alt+F9"); yield 0.5
    shot("n10")
    K("alt+F9"); yield 0.3
    # F9 with everything selected
    K("ctrl+a"); K("F9"); yield 0.6
    check("still saved fine", win.save_to("/tmp/n10b.docx"))
run_scenarios(a)
