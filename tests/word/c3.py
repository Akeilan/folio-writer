exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
from gi.repository import Gdk
ENV = dict(os.environ, DISPLAY=":99")
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
