exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
def fid():
    win.open_file("/tmp/wfid/fid.docx"); yield 4.0
    note("title", win.get_title())
    note("paras", para_texts()[:40])
    check("fidelity file opens with its content", notes() == 1 and notes(True) == 1 and len(objects("Picture")) == 1 and len(comments()) == 1 and pages() == 4,
          (notes(), notes(True), objects(), len(comments()), pages()))
    note("pages", pages())
    caret_start(); yield 0.8
    shot("w4_p1")
    win.canvas.get_vadjustment().set_value(win.canvas.get_vadjustment().get_value() + 900); yield 1.0
    shot("w4_p1b")
    caret_end(); yield 1.0
    shot("w4_plast")
    ok = win.save_to("/tmp/wfid/out.docx"); yield 2.0
    check("saved", ok, ok)
def mathdoc():
    win.open_file("/tmp/wfid/math.docx"); yield 4.0
    check("equations", len(E.ed.all_math()) == 2, len(E.ed.all_math()))
    note("paras", para_texts()[:15])
    caret_start(); yield 0.8
    shot("w4_math")
    ok = win.save_to("/tmp/wfid/math_out.docx"); yield 2.0
    note("saved", ok)
run_scenarios(fid, mathdoc)
