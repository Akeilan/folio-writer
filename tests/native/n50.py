# W5-19: every Office theme is readable - labels against their chrome, title-bar icons
# against the title bar. Measured, not eyeballed.
import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d)))
exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
from gi.repository import Gtk
from folio import icons

THEMES = ["Colorful", "Dark Gray", "Black", "White"]

def _lin(v):
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4

def lum(c):
    """Relative luminance the way WCAG defines it: sRGB linearised first."""
    return 0.2126 * _lin(c.red) + 0.7152 * _lin(c.green) + 0.0722 * _lin(c.blue)

def contrast(a, b):
    x, y = sorted((lum(a) + 0.05, lum(b) + 0.05))
    return y / x

def widgets(w):
    yield w
    if isinstance(w, Gtk.Container):
        for c in w.get_children():
            for x in widgets(c):
                yield x

def find_class(name, kind=None):
    for w in widgets(win):
        if name in w.get_style_context().list_classes() and (kind is None or isinstance(w, kind)):
            yield w

def pb_lum(pb):
    """Mean luminance of an icon's opaque pixels, 0..1 (gamma-encoded, for a rough comparison)."""
    w, h, rs, n = pb.get_width(), pb.get_height(), pb.get_rowstride(), pb.get_n_channels()
    d = pb.get_pixels()
    tot = cnt = 0
    for y in range(h):
        for x in range(w):
            i = y * rs + x * n
            if n < 4 or d[i + 3] > 128:
                tot += 0.2126 * d[i] + 0.7152 * d[i + 1] + 0.0722 * d[i + 2]
                cnt += 1
    return (tot / cnt / 255.0) if cnt else 0.5

def a():
    yield 0.5
    focus()
    for t in THEMES:
        win.app.settings["theme"] = t
        win.app.apply_theme()
        yield 0.8
        tabs = [w for w in find_class("folio-tabs")]
        check("%s: the tab strip is there" % t, bool(tabs))
        bg = tabs[0].get_style_context().get_background_color(Gtk.StateFlags.NORMAL)
        labels = [w for w in find_class("folio-tab") if not isinstance(w, Gtk.Label)]
        worst, who = 99.0, ""
        for w in labels:
            fg = w.get_style_context().get_color(Gtk.StateFlags.NORMAL)
            c = contrast(fg, bg)
            if c < worst:
                worst, who = c, "%s fg=(%.2f,%.2f,%.2f) bg=(%.2f,%.2f,%.2f) classes=%s" % (
                    getattr(w, "name", "?"), fg.red, fg.green, fg.blue, bg.red, bg.green, bg.blue,
                    w.get_style_context().list_classes())
        check("%s: every tab name stands out from the tab strip" % t, worst >= 3.0,
              "worst %.1f:1 on %s" % (worst, who))
        rib = [w for w in find_class("folio-ribbon")]
        rbg = rib[0].get_style_context().get_background_color(Gtk.StateFlags.NORMAL)
        caps = [w for w in find_class("folio-caption")]
        cworst = min([contrast(w.get_style_context().get_color(Gtk.StateFlags.NORMAL), rbg)
                      for w in caps] or [99.0])
        check("%s: group captions stand out from the ribbon" % t, cworst >= 3.0,
              "worst contrast %.1f:1" % cworst)
        # the title bar's own icons
        bar = [w for w in find_class("folio-titlebar")]
        if bar:
            tbg = bar[0].get_style_context().get_background_color(Gtk.StateFlags.NORMAL)
            img = icons.white_image("save", 16)
            pb = img.get_pixbuf()
            if pb is not None:
                d = abs(pb_lum(pb) - lum(tbg))
                check("%s: the title bar icons can be seen on it" % t, d >= 0.3,
                      "icon %.2f vs bar %.2f" % (pb_lum(pb), lum(tbg)))
        # ribbon icons follow the theme
        pb = icons.pixbuf("bold", 16)
        if pb is not None:
            dark_bg = lum(rbg) < 0.5
            ink = pb_lum(pb)
            check("%s: ribbon icons are drawn for this chrome" % t,
                  (ink > 0.5) if dark_bg else (ink < 0.75), "ink %.2f, ribbon %.2f" % (ink, lum(rbg)))
    win.app.settings["theme"] = "Colorful"
    win.app.apply_theme()
run_scenarios(a)
