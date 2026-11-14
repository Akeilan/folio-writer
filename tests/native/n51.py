# W5-13, W5-21: the ribbon is the height it was designed for whatever fonts the computer has,
# and the window fits half a small screen.
import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d)))
exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
from gi.repository import Gtk, Pango

HALF_OF_1366 = 683

def chrome_font():
    """The family the ribbon's own labels are drawn in."""
    for w in (win.ribbon, win.ribbon.tabbar):
        for c in (w.get_children() if isinstance(w, Gtk.Container) else []):
            if isinstance(c, Gtk.Button):
                lab = [x for x in c.get_children() if isinstance(x, Gtk.Label)]
                if lab:
                    return lab[0].get_pango_context().get_font_description().get_family()
    return win.ribbon.get_style_context().get_font(Gtk.StateFlags.NORMAL).get_family()

def narrow():
    yield 0.8
    check("the chrome asks for a font Page ships, so its size is the same everywhere",
          "carlito" in chrome_font().lower(), chrome_font())
    check("the ribbon is its design height", win.ribbon.stack.get_allocated_height() == 96,
          win.ribbon.stack.get_allocated_height())
    mw = win.get_preferred_width()[0]
    check("the window fits half a 1366 px screen", mw <= HALF_OF_1366, mw)
    for w in (1280, 900, 700, 640):
        win.resize(w, 700)
        yield 1.0
        got = win.get_size()[0]
        check("resizing to %d is not refused" % w, got <= max(w, HALF_OF_1366) + 8, got)
        check("  the status bar still shows the page number at %d" % w,
              win.status.widgets["page"].get_visible() or w < 700, w)
        check("  and the view buttons never go" % (), win.status.views_box.get_visible(), w)
    win.resize(1280, 800)
    yield 1.0
    check("wide again, the word count is back", win.status.widgets["words"].get_visible())
run_scenarios(narrow)
