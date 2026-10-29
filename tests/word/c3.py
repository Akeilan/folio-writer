import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
from gi.repository import Gdk
ENV = dict(os.environ, DISPLAY=os.environ.get("DISPLAY", ":99"))
def d():
    p = subprocess.Popen(["xclip", "-selection", "clipboard", "-t", "UTF8_STRING", "-i"], env=ENV, stdin=subprocess.PIPE)
    p.stdin.write(b"External clipboard text"); p.stdin.close()
    yield 1.0
    note("xclip alive", p.poll())
    cb = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
    ok, targets = cb.wait_for_targets()
    note("targets", (ok, [t.name() for t in targets or []]))
    note("text", cb.wait_for_text())
    note("ours", win.app.clipboard().ours())
    t0 = time.time(); img = cb.wait_for_image(); note("image", (img, round(time.time() - t0, 2)))
    yield 0.2
run_scenarios(d)
