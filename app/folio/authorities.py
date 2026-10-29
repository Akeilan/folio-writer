"""References > Table of Authorities: Mark Citation (Alt+Shift+I), Insert
Table of Authorities and Update Table."""
import json

from gi.repository import Gtk

from ._lazy import bridge, docapi
from .widgets import FDialog, combo, grid
from . import modelapi

CATEGORIES = ["Cases", "Statutes", "Other Authorities", "Rules", "Treatises", "Regulations",
              "Constitutional Provisions"]
SECTION = "FolioTOA"


def entries(m):
    try:
        v = json.loads(modelapi._doc_setting(m, "Authorities", "") or "{}")
        return v if isinstance(v, dict) else {}
    except ValueError:
        return {}


def _save(m, e):
    modelapi._set_doc_setting(m, "Authorities", json.dumps(e))


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
    return

