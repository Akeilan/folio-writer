import os as _o; TESTS = _o.environ["FOLIO_WRITER_TESTS"]; exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
def a():
    yield 0.5
    V = win.engine.view
    for f, z in (("pictures", 0.45), ("tables", 0.9), ("breaks", 0.4), ("lists", 1.0)):
        win.open_file("/tmp/corpus/%s.docx" % f); yield 1.5
        V.set_zoom(z); yield 0.8
        shot("cv_" + f)
run_scenarios(a)
