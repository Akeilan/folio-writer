exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
def a():
    yield 1.0
    focus(); yield 0.2
    T("Water boils at 100 degrees"); yield 0.3
    K("ctrl+alt+f"); yield 0.5
    check("in the footnote", E.ed.story() == "notes", E.ed.story())
    T("At sea level."); yield 0.3
    K("Escape"); yield 0.3
    check("back in the text", E.ed.story() == "body")
    T(" Celsius."); yield 0.3
    shot("n9")
    ok = win.save_to("/tmp/n9.docx"); yield 1.0
    import zipfile
    z = zipfile.ZipFile("/tmp/n9.docx")
    fn = z.read("word/footnotes.xml").decode()
    d = z.read("word/document.xml").decode()
    check("note text", "At sea level." in fn, fn[-400:])
    check("reference", "w:footnoteReference" in d)
    check("text after", "Celsius" in d and d.index("footnoteReference") < d.index("Celsius"), d[-600:])
run_scenarios(a)
