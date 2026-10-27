exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
def fid():
    win.open_file("/tmp/wfid/fid.docx"); yield 4.0
    m = M()
    note("title", win.get_title())
    note("paras", para_texts()[:40])
    note("tables", m.getTextTables().getCount())
    note("graphics", m.getGraphicObjects().getCount())
    n = 0; en = m.getTextFields().createEnumeration()
    while en.hasMoreElements():
        f = en.nextElement(); n += f.supportsService("com.sun.star.text.textfield.Annotation")
    note("comments", n)
    note("pages", vc().jumpToLastPage() and vc().getPage())
    vc().jumpToFirstPage(); vc().gotoStart(False); yield 0.8
    shot("w4_p1")
    win.canvas.get_vadjustment().set_value(win.canvas.get_vadjustment().get_value() + 900); yield 1.0
    shot("w4_p1b")
    vc().jumpToLastPage(); yield 1.0
    shot("w4_plast")
    ok = win.save_to("/tmp/wfid/out.docx"); yield 2.0
    note("saved", ok)
def mathdoc():
    win.open_file("/tmp/wfid/math.docx"); yield 4.0
    note("formulas", len(docapi.formulas(M())))
    note("paras", para_texts()[:15])
    vc().gotoStart(False); yield 0.8
    shot("w4_math")
    ok = win.save_to("/tmp/wfid/math_out.docx"); yield 2.0
    note("saved", ok)
run_scenarios(fid, mathdoc)
