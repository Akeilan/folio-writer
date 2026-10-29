import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
e = win.engine
win_events = []
e.view.connect("window", lambda v, p: log("WINDOW", p[:200]))
e.connect("engine-dialog", lambda en, t: log("ENGINE DIALOG", t))
def s1(): e.command(".uno:InsertTable", {"Columns": ("long", 2), "Rows": ("long", 2)})
def s2(): log("before split"); e.command(".uno:SplitCell")
def s3(): e.command(".uno:InsertText", {"Text": "after"})
def s4():
    m = e.model
    log("text now", repr(m.getText().getString()[:80]))
    shot("t7")
    app.quit()
steps(s1, s2, s3, s4, delay=2000)
