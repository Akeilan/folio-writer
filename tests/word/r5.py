import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
def d():
    win.open_file("/tmp/wfid/math.docx"); yield 8.0
    xs = [E.ed.math_xml(n) for n in E.ed.all_math()]
    check("equations imported as Office Math", len(xs) > 0 and all("m:oMath" in x for x in xs), len(xs))
    check("fractions kept", len(xs) == 2 and all("m:f>" in x or "<m:f>" in x for x in xs), [x[:80] for x in xs])
    check("document not marked modified", not modified(), modified())
    win.canvas.get_vadjustment().set_value(0); yield 1.0
    shot("r5_math")
run_scenarios(d)
