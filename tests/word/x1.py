exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
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
