import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
import subprocess
def x(*a): subprocess.run(["xdotool"] + list(a), env=dict(os.environ, DISPLAY=":99"))
def s0():
    win.present(); win.focus_document(); x("type", "--delay", "40", "above")
def s1(): x("key", "Return"); x("type", "--delay", "60", "--", "---")
def s1b(): log("before enter", repr(win.engine.model.getText().getString())); x("key", "Return"); x("type","--delay","40","below")
def s2():
    en = win.engine.model.getText().createEnumeration()
    while en.hasMoreElements():
        p = en.nextElement(); b = p.BottomBorder; t = p.TopBorder
        log(repr(p.getString()), "bottom", b.LineWidth, b.OuterLineWidth, "top", t.LineWidth, p.ParaStyleName)
    shot("border"); app.quit()
steps(s0, s1, s1b, s2, delay=3000)
