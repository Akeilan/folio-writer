import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
from folio import docapi
A = win.actions
def s0(): win.unmaximize(); win.resize(1590, 960); win.move(0,0); A.insert_text("Body text.")
def s1(): win.run("header")
def s2(): A.insert_text("My header"); log("in hf", win.in_header_footer(), "tab", win.ribbon.current.name)
def s3(): shot("hf1"); win.hf_checks["first"].set_active(True)
def s4():
    log("opts", docapi.hf_options(win.engine.model)); win.hf_spins["header_top"].set_value(2000)
def s5():
    log("opts", docapi.hf_options(win.engine.model)); win.run("close-header-footer")
def s6(): log("in hf", win.in_header_footer(), "tab", win.ribbon.current.name); shot("hf2"); app.quit()
steps(s0, s1, s2, s3, s4, s5, s6, delay=2000)
