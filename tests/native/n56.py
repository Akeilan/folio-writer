import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
# W5-05: a table saved as .doc and reopened is the table that was saved.
import os

def fill(rows, cols):
    fresh()
    ed = E.ed
    ed.insert_table(rows, cols)
    E.view.after_edit()
    cells = table_paras(0)
    for r in range(rows):
        for c in range(cols):
            p = cells[r][c][0]
            ed.select_nodes(p, 0, p, 0)
            ed.type_text("r%dc%d" % (r, c))
    E.view.after_edit()
    return tables()

def trip(path):
    win.save_to(path)
    return path

def a():
    yield 1.0
    focus(); yield 0.2
    ed = E.ed
    for rows, cols in ((3, 3), (2, 4)):
        want = fill(rows, cols); yield 0.5
        trip("/tmp/n56_%dx%d.doc" % (rows, cols)); yield 2.5
        win.engine.open("/tmp/n56_%dx%d.doc" % (rows, cols)); yield 3.0
        got = tables()
        check("%dx%d: one table" % (rows, cols), len(got) == 1, str(got))
        check("%dx%d: the rows came back" % (rows, cols), got and len(got[0]) == rows, str(got))
        check("%dx%d: the cells came back" % (rows, cols),
              got and all(len(r) == cols for r in got[0]), str(got))
        check("%dx%d: the words came back" % (rows, cols), got == want, "%s -> %s" % (want, got))
        check("%dx%d: no stray paragraphs" % (rows, cols),
              [t for t in para_texts() if t.strip()] == ["<table>"], str(para_texts()))
    # text around the table keeps its place
    fresh()
    ed = E.ed
    ed.type_text("before\n")
    ed.insert_table(2, 2)
    E.view.after_edit(); yield 0.4
    cells = table_paras(0)
    for r in range(2):
        for c in range(2):
            p = cells[r][c][0]
            ed.select_nodes(p, 0, p, 0); ed.type_text("c%d%d" % (r, c))
    ed.move_caret("doc_end", False)
    ed.type_text("after")
    E.view.after_edit(); yield 0.4
    want = tables()
    trip("/tmp/n56_mix.doc"); yield 2.5
    win.engine.open("/tmp/n56_mix.doc"); yield 3.0
    got = tables()
    check("a table between paragraphs keeps its shape", got == want, "%s -> %s" % (want, got))
    texts = [t for t in para_texts() if t.strip()]
    check("the text around it is in order", texts == ["before", "<table>", "after"], str(texts))
    # the .doc files the suite keeps still read
    corpus = "/tmp/corpus/lo"
    if os.path.isdir(corpus):
        for name in sorted(os.listdir(corpus)):
            if not name.endswith(".doc"):
                continue
            win.engine.open(os.path.join(corpus, name)); yield 2.0
            check("%s still opens" % name, win.engine.ed is not None and not win.engine.open_error,
                  str(win.engine.open_error))
    E.ed.mark_saved()

run_scenarios(a)
