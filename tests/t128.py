import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
def s0(): win.actions.insert_text("Green theme check.")
def s1(): shot("t128a"); win.run("backstage-open") if False else win.backstage.open() if hasattr(win.backstage,"open") else None
def s2(): shot("t128b"); app.quit()
steps(s0, s1, s2, delay=2000)
