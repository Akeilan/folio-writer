exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
def a():
    yield 1.0
    focus(); yield 0.2
    ed = E.ed
    ed.type_text("Plain bold text\n")
    ed.move_caret("doc_start", False)
    for _ in range(6):
        ed.move_caret("right", False)
    for _ in range(4):
        ed.move_caret("right", True)
    E.view.after_move()
    K("ctrl+b"); yield 0.3
    K("ctrl+c"); yield 0.3
    ed.move_caret("doc_end", False); E.view.after_move()
    K("ctrl+v"); yield 0.5
    ids = None
    import zipfile
    win.save_to("/tmp/n14.docx"); yield 0.6
    d = zipfile.ZipFile("/tmp/n14.docx").read("word/document.xml").decode()
    check("paste kept bold", d.count("<w:b/>") >= 2, d[-600:])
    # an equation, then convert all to linear and back
    ed.move_caret("doc_end", False)
    ed.type_text("\n")
    E.view.after_edit()
    K("alt+equal"); yield 0.6
    T("a^2+b^2=c^2 "); yield 0.6
    K("Escape"); yield 0.5
    mid = ed.all_math()[0]
    win.eqbar.convert_all("linear"); yield 0.5
    x = ed.math_xml(mid)
    check("linear form", "<m:sSup>" not in x and "a^2" in x, x[:300])
    win.eqbar.convert_all("professional"); yield 0.5
    x = ed.math_xml(mid)
    check("professional again", "<m:sSup>" in x, x[:300])
    # a red equation keeps its colour when edited
    red = '<m:oMath xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><m:r><w:rPr><w:color w:val="FF0000"/></w:rPr><m:t>y</m:t></m:r></m:oMath>'
    ed.move_caret("doc_end", False)
    ed.type_text("\nRed: ")
    rid = ed.insert_math(red, False)
    E.view.document_changed(); yield 0.3
    from folio.native.equations import NativeEq
    win.eqbar.ed.start(NativeEq(E, rid)); yield 0.5
    K("End"); T("+1"); yield 0.5
    K("Escape"); yield 0.5
    x = ed.math_xml(rid)
    check("colour kept", "FF0000" in x and "1" in x, x)
    shot("n14")
run_scenarios(a)
