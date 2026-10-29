import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
def s0(): app.settings["qat"] = [k for k, *_ in win.QAT_COMMANDS]; win.build_qat()
steps(s0, lambda: (shot("t133"), app.settings.__setitem__("qat", ["save","undo","redo"]), app.save_settings(), app.quit()), delay=2000)
