import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
KL = []
win.connect("key-press-event", lambda w, e: KL.append((Gdk.keyval_name(e.keyval), int(e.state), e.hardware_keycode)) and False)
from gi.repository import Gdk
def d():
    fresh(); yield 0.4
    T("-abc", delay=80); yield 0.8
    note("keys", KL); note("text", para_texts())
    del KL[:]
    fresh(); yield 0.4
    T("x-abc", delay=80); yield 0.8
    note("keys2", KL); note("text2", para_texts())
run_scenarios(d)
