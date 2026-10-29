import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
e = win.engine
def s1():
    e.command(".uno:InsertText", {"Text": "The quadratic formula: "})
def s2():
    win.eqbar.new_equation("x=(-b±√(b^2-4ac))/2a")
def s3():
    shot("eq1")
    win.eqbar.finish()
    e.command(".uno:InsertText", {"Text": " is famous."})
def s4():
    e.command(".uno:InsertPara")
    win.eqbar.new_equation()
def s5():
    import subprocess
    subprocess.run(["xdotool", "type", "--delay", "30", "\\sum _(i=1)^n i^2=(n(n+1)(2n+1))/6 "])
def s6():
    log("entry:", win.eqbar.entry.get_text())
    shot("eq2")
    win.eqbar.finish()
def s7():
    from folio import docapi
    objs = docapi.formulas(win.engine.model)
    log("formulas", len(objs), [docapi.formula_of(o) for o in objs])
    docapi.select_object(win.engine.model, objs[0])
def s8():
    log("bar open after select:", win.eqbar.ed.active, repr(win.eqbar.entry.get_text()))
    shot("eq3")
    win.eqbar.finish()
    e.save_as("/tmp/eqtest.docx", "docx", keep=False)
    import zipfile
    x = zipfile.ZipFile("/tmp/eqtest.docx").read("word/document.xml").decode()
    log("docx omath count", x.count("<m:oMath>"), x.count("<m:oMath"))
    app.quit()
steps(s1, s2, s3, s4, s5, s6, s7, s8, delay=1500)
