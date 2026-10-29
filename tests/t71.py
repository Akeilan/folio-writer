import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
from folio import docapi
A = win.actions; m = lambda: win.engine.model
def s0():
    for h, body in (("Alpha", "alpha body"), ("Beta", "beta body"), ("Gamma", "gamma body")):
        A.apply_style("Heading 1"); A.insert_text(h); A.cmd(".uno:InsertPara"); A.apply_style("Normal"); A.insert_text(body); A.cmd(".uno:InsertPara")
def s1():
    hs = docapi.headings(m()); log([h[1] for h in hs])
    docapi.move_section(m(), hs[2][2], hs[0][2], after=False)
def s2():
    log("after move gamma first", repr(m().getText().getString()))
    hs = docapi.headings(m()); docapi.move_section(m(), hs[0][2], hs[2][2], after=True)
def s3(): log("after move gamma last", repr(m().getText().getString())); win.run("new-window")
def s4():
    wins = [w for w in Gtk.Window.list_toplevels() if w.get_visible() and ":2" in (w.get_title() or "")]
    log("new window", [w.get_title() for w in wins]); app.quit()
steps(s0, s1, s2, s3, s4, delay=2500)
