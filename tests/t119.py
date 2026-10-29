import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
from folio import docapi
e = win.engine; m = lambda: e.model
def typ(s): return lambda: subprocess.run(["xdotool", "type", "--delay", "40", s])
def key(*k): return lambda: subprocess.run(["xdotool", "key", "--delay", "60"] + list(k))
def chk(n): return lambda: (log(n, "active", win.eqbar.ed.active, "mode", win.eqbar.ed.mode, "lin", repr(win.eqbar.entry.get_text()), "frame", win.eqbar.ed.frame), shot(n))
def s0():
    win.actions.insert_text("Intro text."); e.command(".uno:InsertPara")
    win.focus_document()
steps(s0, lambda: win.run("equation"), chk("eq0"), typ("x=(-b+-\\sqrt (b^2-4ac))/2a "), chk("eq1b"), typ("+\\alpha "), chk("eq1"),
      key("Escape"), chk("eq2"),
      lambda: log("formulas", [docapi.formula_of(o) for o in docapi.formulas(m())]),
      lambda: app.quit(), delay=1500)
