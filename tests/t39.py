import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
def s0():
    out = sorted({(c.tooltip_text or "") for c in win.ribbon.all_controls()})
    log(len(out)); log(" | ".join(out)); app.quit()
steps(s0, delay=1000)
