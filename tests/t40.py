import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
import subprocess
def x(*a): subprocess.run(["xdotool"] + list(a), env=dict(os.environ, DISPLAY=":99"))
def s0(): win.unmaximize(); win.resize(1590,960); win.move(0,0)
def s1(): x("mousemove", "186", "140")
def s2(): x("mousemove", "188", "141")
def s3(): shot("tip"); app.quit()
steps(s0, s1, s2, s3, delay=1500)
