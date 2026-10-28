"""References > Table of Authorities: Mark Citation (Alt+Shift+I), Insert
Table of Authorities and Update Table."""
import json

from gi.repository import Gtk

from ._lazy import bridge, docapi
from .widgets import FDialog, combo, grid

CATEGORIES = ["Cases", "Statutes", "Other Authorities", "Rules", "Treatises", "Regulations",
              "Constitutional Provisions"]
SECTION = "FolioTOA"


def entries(m):
    try:
        v = json.loads(docapi._doc_setting(m, "Authorities", "") or "{}")
        return v if isinstance(v, dict) else {}
    except ValueError:
        return {}


def _save(m, e):
    docapi._set_doc_setting(m, "Authorities", json.dumps(e))


def _new_id(e):
    n = 1
    while "TA%d" % n in e:
        n += 1
    return "TA%d" % n


def _bookmark(m, rng, name):
    bm = m.createInstance("com.sun.star.text.Bookmark")
    bm.setName(name)
    rng.getText().insertTextContent(rng, bm, True)


def mark(m, rng, long_cite, short_cite, category, all_occurrences=False):
    e = entries(m)
    eid = next((k for k, v in e.items() if v["long"] == long_cite), None) or _new_id(e)
    e[eid] = {"long": long_cite, "short": short_cite or long_cite, "cat": category}
    marks = m.getBookmarks()
    um = m.getUndoManager()
    um.enterUndoContext("Mark Citation")
    try:
        k = 1
        while marks.hasByName("_%s_%d" % (eid, k)):
            k += 1
        _bookmark(m, rng, "_%s_%d" % (eid, k))
        count = 1
        if all_occurrences:
            for needle in {long_cite, short_cite} - {""}:
                sd = m.createSearchDescriptor()
                sd.SearchString = needle
                sd.SearchCaseSensitive = True
                found = m.findAll(sd)
                for i in range(found.getCount()):
                    f = found.getByIndex(i)
                    if _marked(m, f):
                        continue
                    k += 1
                    while marks.hasByName("_%s_%d" % (eid, k)):
                        k += 1
                    _bookmark(m, f, "_%s_%d" % (eid, k))
                    count += 1
        _save(m, e)
        return count
    finally:
        um.leaveUndoContext()


def _marked(m, rng):
    marks = m.getBookmarks()
    text = rng.getText()
    for n in marks.getElementNames():
        if not n.startswith("_TA"):
            continue
        a = marks.getByName(n).getAnchor()
        try:
            if a.getText() == text and text.compareRegionStarts(a.getStart(),
                                                                rng.getStart()) == 0:
                return True
        except Exception:
            pass
    return False






# ------------------------------------------------------------ dialogs
def mark_dialog(win):
    m = win.engine.model
    if m is None:
        return
    vc = docapi.view_cursor(m)
    sel = vc.getString().strip()
    d = FDialog(win, "Mark Citation", buttons=(("Mark", 10), ("Mark All", 11),
                                               ("Close", Gtk.ResponseType.CANCEL)))
    long_tv = Gtk.TextView()
    long_tv.set_wrap_mode(Gtk.WrapMode.WORD)
    long_tv.set_size_request(380, 60)
    long_tv.get_buffer().set_text(sel)
    fr = Gtk.Frame()
    fr.add(long_tv)
    d.add(Gtk.Label(label="Selected text:", xalign=0))
    d.add(fr)
    cat = combo(CATEGORIES, 0)
    short = Gtk.Entry(text=sel)
    d.add(grid([["_Category:", cat], ["_Short citation:", short]]))
    while True:
        r = d.ask()
        if r not in (10, 11):
            break
        b = long_tv.get_buffer()
        long_cite = b.get_text(*b.get_bounds(), False).strip()
        if not long_cite or vc.isCollapsed():
            win.dialogs.message("Select the citation in the document first.")
            continue
        n = mark(m, vc, long_cite, short.get_text().strip(), cat.get_active_text(),
                 all_occurrences=(r == 11))
        win.status.flash("Marked %d citation%s." % (n, "" if n == 1 else "s"))
        if r == 11:
            break
    d.done()

