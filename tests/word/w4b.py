exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
def fid():
    win.open_file("/tmp/wfid/fid.docx"); yield 4.0
    t = M().getText(); en = t.createEnumeration(); c = vc()
    while en.hasMoreElements():
        p = en.nextElement()
        if not p.supportsService("com.sun.star.text.Paragraph"): continue
        c.gotoRange(p.getStart(), False)
        note("para", (c.getPage(), p.getString()[:30], p.PageDescName, p.BreakType.value, p.PageStyleName))
    c.jumpToLastPage(); note("last page", c.getPage())
    n = 0; en = M().getTextFields().createEnumeration()
    while en.hasMoreElements():
        f = en.nextElement()
        if f.supportsService("com.sun.star.text.textfield.Annotation"): note("comment", (f.Author, repr(f.Content), f.DateTimeValue.Hours))
    for nm in M().getStyleFamilies().getByName("PageStyles").getElementNames():
        s = M().getStyleFamilies().getByName("PageStyles").getByName(nm)
        if s.isInUse(): note("pagestyle", (nm, s.PageStyleLayout.value if hasattr(s.PageStyleLayout,'value') else s.PageStyleLayout, s.IsLandscape))
run_scenarios(fid)
