import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
from folio import docapi
A = win.actions; m = lambda: win.engine.model
seen = {}
win.engine.connect("state-changed", lambda e, k, v: seen.__setitem__(k, v))
def s0(): A.insert_text("Text before picture. ")
def s1(): seen.clear(); docapi.insert_picture(m(), "/tmp/pic.png")
def s2():
    log({k: v for k, v in seen.items() if any(w in k for w in ("Pos", "Size", "Rect", "Graphic", "Trans"))})
    vc = m().getCurrentController().getViewCursor(); p = vc.getPosition(); log("vc pos", p.X, p.Y)
    log("all keys", sorted(seen.keys())[:80])
    app.quit()
steps(s0, s1, s2, delay=2500)
