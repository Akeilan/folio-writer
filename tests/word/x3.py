exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
def d():
    win.open_file("/tmp/wfid/math.docx"); yield 5.0
    for i, o in enumerate(docapi.formulas(M())):
        note("f%d" % i, o.Model.Formula)
run_scenarios(d)
