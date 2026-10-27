exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
import zipfile
def a():
    yield 1.0
    focus(); yield 0.2
    ed = E.ed
    ed.type_text("Energy: ")
    E.view.after_edit(); yield 0.2
    K("alt+equal"); yield 0.8
    check("editing", win.eqbar.ed.active)
    T("E=mc^2 "); yield 0.8
    K("Escape"); yield 0.6
    check("left editor", not win.eqbar.ed.active)
    ids = ed.all_math()
    check("one equation", len(ids) == 1, str(ids))
    x = ed.math_xml(ids[0]) if ids else ""
    check("omml written", "<m:sSup>" in x and "E" in x, x[:300])
    ed.move_caret("doc_end", False)
    ed.type_text("\n")
    E.view.after_edit(); yield 0.3
    # a display equation in an empty paragraph
    K("alt+equal"); yield 0.8
    T("x=(-b+-\\sqrt (b^2-4ac))/2a#(1) "); yield 1.0
    K("Escape"); yield 0.6
    ids = ed.all_math()
    check("two equations", len(ids) == 2, str(ids))
    inf = ed.math_info(ids[1]) if len(ids) > 1 else None
    check("display", bool(inf and inf["display"]), str(inf))
    check("numbered", "#" in ed.math_xml(ids[1]) and "eqArr" in ed.math_xml(ids[1]) if len(ids) > 1 else False)
    shot("n12")
    win.save_to("/tmp/n12.docx"); yield 0.8
    d = zipfile.ZipFile("/tmp/n12.docx").read("word/document.xml").decode()
    check("saved", d.count("<m:oMath>") + d.count("<m:oMath ") == 2 and "m:oMathPara" in d)
    check("namespace", 'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"' in d)
    # click the first equation to edit it again
    inf = ed.math_info(ids[0])
    px, py = E.view.to_widget(inf["page"], inf["x"] + inf["w"] - 1, inf["base"] - 2)
    sx, sy = screen_of_widget(E.view, px, py)
    X("mousemove", int(sx), int(sy)); X("click", "1"); yield 0.8
    check("click edits", win.eqbar.ed.active)
    K("End"); T("+1"); yield 0.6
    K("Escape"); yield 0.6
    check("edited", "+" in ed.math_xml(ids[0]) or "1" in ed.math_xml(ids[0]))
    ed.undo(); E.view.after_edit(); yield 0.3
run_scenarios(a)
