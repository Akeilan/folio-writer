import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
from folio import grammar
A = win.actions; m = lambda: win.engine.model
def s0(): A.insert_text("This is is a test.  i went to a apple store,and bought things. He should of known. It was an university.")
def s1():
    log("check", grammar.check(m().getText().getString()))
    win.run("spelling")
def s2():
    from folio.panes import EditorPane
    p = win.panes[EditorPane]; log("pane", p.status.get_text(), p.current)
    for i in range(8):
        p.ignore_once(); log("next", p.status.get_text(), p.current)
    log("rows", len(p.sugg.get_children()))
    app.quit()
steps(s0, s1, s2, delay=2500)
