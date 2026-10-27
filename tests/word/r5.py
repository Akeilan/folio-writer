exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
def d():
    win.open_file("/tmp/wfid/math.docx"); yield 8.0
    fs = [o.Model.Formula for o in docapi.formulas(M())]
    bad = [f for f in fs if __import__("folio.mathfix", fromlist=["x"])._bare_froms(f)]
    check("no operator-less n-ary left", not bad, bad)
    note("fixed", [f for f in fs if "oper" in f])
    check("document not marked modified", not M().isModified(), M().isModified())
    win.canvas.get_vadjustment().set_value(0); yield 1.0
    shot("r5_math")
run_scenarios(d)
