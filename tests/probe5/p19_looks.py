import os as _o; TESTS = _o.environ["FOLIO_WRITER_TESTS"]; exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read()); exec(open("/tmp/p5/probes/ph.py").read())
def a():
    yield 0.5
    win.open_file("/tmp/corpus/styles.docx"); yield 1.5
    win.app.settings["theme"] = "Black"; win.app.apply_theme(); yield 1.0
    shot("look_black")
    win.resize(820, 600); yield 1.0
    shot("look_narrow_black")
    win.app.settings["theme"] = "Colorful"; win.app.apply_theme(); yield 0.6
    shot("look_narrow")
    win.resize(560, 420); yield 1.0
    shot("look_tiny")
    note("size at tiny", win.get_size())
    win.resize(1290, 870); yield 0.5
    win.show_backstage("info") if hasattr(win, "show_backstage") else win.run("backstage"); yield 1.5
    shot("look_info")
run_scenarios(a)
