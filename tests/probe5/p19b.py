import os as _o; TESTS = _o.environ["FOLIO_WRITER_TESTS"]; exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
def a():
    yield 0.5
    win.open_file("/tmp/corpus/styles.docx"); yield 1.5
    for t in ("Dark Gray", "White"):
        win.app.settings["theme"] = t; win.app.apply_theme(); yield 1.0
        subprocess.run(["import", "-window", "root", "-crop", "1290x200+0+0", "/tmp/p5shot_theme_%s.png" % t.replace(" ", "")], env=dict(os.environ))
run_scenarios(a)
