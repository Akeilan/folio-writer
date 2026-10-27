exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
def a():
    yield 1.0
    focus(); yield 0.2
    T("A table follows."); K("Return"); yield 0.3
    win.dialogs._new_table(3, 3); yield 0.5
    check("caret in table", E.ed.cell_name() == "A1", E.ed.cell_name())
    T("Name"); K("Tab"); T("Qty"); K("Tab"); T("Price"); K("Tab"); yield 0.3
    T("Apples"); K("Tab"); T("3"); yield 0.3
    check("cell B2", E.ed.cell_name() == "B2", E.ed.cell_name())
    win.run(".uno:InsertRowsAfter"); yield 0.3
    win.run(".uno:InsertColumnsAfter"); yield 0.3
    check("table tab shown", E.get(".uno:StateTableCell") != "", E.get(".uno:StateTableCell"))
    ok = win.save_to("/tmp/n5.docx"); yield 1.0
    check("saved", ok)
    shot("n5")
    import zipfile
    x = zipfile.ZipFile("/tmp/n5.docx").read("word/document.xml").decode()
    check("rows/cols", x.count("<w:tr") == 4 and x.count("<w:gridCol") == 4, (x.count("<w:tr"), x.count("<w:gridCol")))
run_scenarios(a)
