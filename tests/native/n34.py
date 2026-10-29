import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
# 2.31: field codes shown and edited in place, as in Word (W2-04)
import zipfile


def body(ed):
    return [ed.para_text_of(n) for k, n, _t in ed.body_blocks() if k == "p"]


def a():
    yield 1.0
    focus(); yield 0.2
    fresh(); yield 0.2
    ed = E.ed
    T("Page "); yield 0.2
    ed.insert_field_now("PAGE \\* MERGEFORMAT"); E.view.after_edit(); yield 0.3
    T(" of "); yield 0.2
    ed.insert_field_now("NUMPAGES \\* MERGEFORMAT"); E.view.after_edit(); yield 0.3
    check("results", body(ed)[0] == "Page 1 of 1", body(ed))
    # ---- Alt+F9: codes as text in the document
    K("alt+F9"); yield 0.5
    t = body(ed)[0]
    check("Alt+F9 shows the codes as text", "PAGE \\* MERGEFORMAT" in t and "NUMPAGES" in t and "1 of" not in t, t)
    shot("n34_codes"); yield 0.2
    # put the caret in the first code, after PAGE, and edit it
    i = t.index("PAGE") + len("PAGE")
    p0 = ed.body_blocks()[0][1]
    ed.select_nodes(p0, i, p0, i); E.view.after_move(); yield 0.2
    T("REF"); yield 0.3
    t2 = body(ed)[0]
    check("typing goes into the code", "PAGEREF \\* MERGEFORMAT" in t2, t2)
    K("BackSpace"); K("BackSpace"); K("BackSpace"); yield 0.3
    check("backspace edits the code", "PAGE \\* MERGEFORMAT" in body(ed)[0] and "PAGEREF" not in body(ed)[0], body(ed))
    # change the second field into a date
    t = body(ed)[0]
    j = t.index("NUMPAGES")
    ed.select_nodes(p0, j, p0, j + len("NUMPAGES")); E.view.after_move(); yield 0.2
    T("DATE"); yield 0.3
    check("the second code replaced", "DATE \\* MERGEFORMAT" in body(ed)[0], body(ed))
    win.save_to("/tmp/n34.docx"); yield 0.8
    x = zipfile.ZipFile("/tmp/n34.docx").read("word/document.xml").decode()
    check("the code is saved as the field's instruction", "DATE \\* MERGEFORMAT" in x and "<w:instrText" in x
          and x.count("<w:instrText") == 2, x[x.find("<w:body"):][:600])
    K("alt+F9"); yield 0.5
    K("ctrl+a"); K("F9"); yield 0.6
    import datetime
    d = datetime.date.today()
    check("F9 works the new code out", body(ed)[0].startswith("Page 1 of ") and str(d.year) in body(ed)[0], body(ed))
    # ---- Shift+F9: just the field at the cursor
    K("ctrl+Home"); K("Right"); K("Right"); K("Right"); K("Right"); K("Right"); yield 0.2
    K("shift+F9"); yield 0.5
    t = body(ed)[0]
    check("Shift+F9 shows one field's code", "PAGE \\* MERGEFORMAT" in t and "DATE" not in t, t)
    K("shift+F9"); yield 0.5
    check("and its result again", body(ed)[0].startswith("Page 1 of"), body(ed))
    # ---- Ctrl+F9 with text selected
    K("End"); T(" NUMPAGES"); K("ctrl+shift+Left"); yield 0.2
    K("ctrl+F9"); yield 0.4
    check("Ctrl+F9 puts the selection in the braces", body(ed)[0].endswith(" NUMPAGES ") and ed.codes_shown()[1] == 1,
          (body(ed), ed.codes_shown()))
    K("F9"); yield 0.5
    check("F9 shows its result", body(ed)[0].endswith(" 1") and ed.codes_shown()[1] == 0, (body(ed), ed.codes_shown()))
    # ---- undo
    K("ctrl+z"); yield 0.4
    ed.mark_saved()


run_scenarios(a)
