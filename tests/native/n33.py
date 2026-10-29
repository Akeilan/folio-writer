import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
# 2.31: the ribbon is the suite's: 96 px tall on every tab, three rows at most (W2-07)
from gi.repository import Gtk
from folio import ribbon as R


def groups(w, out):
    if isinstance(w, R.Group):
        out.append(w)
        return out
    if isinstance(w, Gtk.Container):
        for c in w.get_children():
            groups(c, out)
    return out


def a():
    yield 1.0
    st = win.ribbon.stack
    tall = []
    for page in st.get_children():
        nm = st.child_get_property(page, "name")
        h = page.get_preferred_height()[1]
        if h > 96:
            tall.append((nm, h, [(g.caption, g.get_preferred_height()[1]) for g in groups(page, [])
                                 if g.get_preferred_height()[1] > 96]))
    check("every tab fits the 96 px ribbon body", not tall, tall)
    check("ribbon body is 96 px", st.get_allocated_height() == 96, st.get_allocated_height())
    for name in ("Home", "Insert", "Layout", "References", "Review", "Mailings"):
        win.ribbon.select([t for t in win.ribbon.tabs if t.name == name][0]); yield 0.4
        check("%s tab body 96 px" % name, st.get_allocated_height() == 96, st.get_allocated_height())
        shot("n33_" + name.lower()); yield 0.1
    win.ribbon.select([t for t in win.ribbon.tabs if t.name == "Home"][0]); yield 0.2


run_scenarios(a)
