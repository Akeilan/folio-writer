exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
def d():
    win.open_file("/tmp/wfid/math.docx"); yield 8.0
    xs = [E.ed.math_xml(n) for n in E.ed.all_math()]
    check("equations imported as Office Math", len(xs) > 0 and all("m:oMath" in x for x in xs), len(xs))
    check("fractions kept", len(xs) == 2 and all("m:f>" in x or "<m:f>" in x for x in xs), [x[:80] for x in xs])
    check("document not marked modified", not modified(), modified())
    win.canvas.get_vadjustment().set_value(0); yield 1.0
    shot("r5_math")
run_scenarios(d)
