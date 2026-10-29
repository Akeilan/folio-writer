import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
import zipfile
def a():
    yield 1.0
    focus(); yield 0.2
    ed = E.ed
    for i in range(80):
        ed.type_text("Line %d of a document with mirrored margins and an art border.\n" % i)
    E.view.after_edit(); yield 0.4
    win.actions.run(("margins", "mirrored")); yield 0.5
    check("mirror on", ed.setting("mirrorMargins"))
    ps = ed.page_setup(0)
    check("inside 1.25in", ps["left"] == 1800, ps)
    win.actions.run(("orientation", True)); yield 0.4
    ps = ed.page_setup(0)
    check("landscape", ps["width"] > ps["height"], ps)
    win.actions.run(("orientation", False)); yield 0.4
    win.actions.run(("columns", 2)); yield 0.4
    check("two columns", ed.page_setup(0)["cols"] == 2)
    win.actions.run(("columns", 1)); yield 0.4
    xml = ('<w:pgBorders w:offsetFrom="page"><w:top w:val="apples" w:sz="20" w:space="24"/>'
           '<w:left w:val="apples" w:sz="20" w:space="24"/><w:bottom w:val="apples" w:sz="20" w:space="24"/>'
           '<w:right w:val="apples" w:sz="20" w:space="24"/></w:pgBorders>')
    ed.set_page_borders(None, xml)
    E.view.document_changed(); yield 0.5
    win.run("multiple-pages"); yield 0.8
    shot("n17")
    K("Escape"); yield 0.3
    win.save_to("/tmp/n17.docx"); yield 0.8
    z = zipfile.ZipFile("/tmp/n17.docx")
    d = z.read("word/document.xml").decode()
    s = z.read("word/settings.xml").decode()
    check("pgBorders saved", 'w:val="apples"' in d)
    check("mirrorMargins saved", "w:mirrorMargins" in s)
run_scenarios(a)
