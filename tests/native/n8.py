exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
def a():
    yield 1.0
    focus(); yield 0.2
    for i in range(45):
        E.ed.type_text("Paragraph %d of the body text that fills the pages.\n" % (i + 1))
    E.view.after_edit(); yield 0.5
    check("two pages", E.ed.page_count() >= 2, E.ed.page_count())
    from folio import pagenum
    pagenum.insert(win, "bottom", "center", "xofy"); yield 0.5
    check("footer on every page", all(E.ed.page_hf(i)[1] for i in range(E.ed.page_count())))
    # double-click the top margin of page 2: a header to type in
    v = E.view
    x, y = v.to_widget(1, 300, 30)
    import gi
    from gi.repository import Gdk
    ev = Gdk.Event.new(Gdk.EventType._2BUTTON_PRESS)
    ev.button.button = 1; ev.button.x = x; ev.button.y = y
    v.emit("button-press-event", ev); yield 0.4
    check("editing header", E.ed.story() == "hf" and E.ed.story_page() == 1, E.ed.story())
    check("Header & Footer tab", getattr(win, "_native_hf", False))
    T("Confidential"); yield 0.4
    shot("n8")
    K("Escape"); yield 0.3
    check("back in body", E.ed.story() == "body")
    ok = win.save_to("/tmp/n8.docx"); yield 1.0
    import zipfile
    z = zipfile.ZipFile("/tmp/n8.docx")
    names = z.namelist()
    hdr = [n for n in names if n.startswith("word/header")]
    ftr = [n for n in names if n.startswith("word/footer")]
    check("parts saved", hdr and ftr, names)
    check("header text", "Confidential" in z.read(hdr[0]).decode())
    check("page field", "NUMPAGES" in z.read(ftr[0]).decode())
    d = z.read("word/document.xml").decode()
    check("references", "w:headerReference" in d and "w:footerReference" in d)
run_scenarios(a)
