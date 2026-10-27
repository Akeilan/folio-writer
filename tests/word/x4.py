exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
from folio import mathfix
mathfix.fix_document = lambda m, p: 0
def d():
    win.open_file("/tmp/wfid/math.docx"); yield 6.0
    note("modified without fix", M().isModified())
    win.open_file("/tmp/wfid/fid.docx"); yield 6.0
    note("fid modified", M().isModified())
run_scenarios(d)
