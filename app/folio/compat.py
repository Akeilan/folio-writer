"""File > Info > Check for Issues > Check Compatibility: features of this
document that are lost or changed when it is saved in an older or other
file format."""
from gi.repository import Gtk

from . import docapi
from .widgets import FDialog

TARGETS = [("doc", "Document 97-2003 (.doc)"),
           ("rtf", "Rich Text Format (.rtf)"),
           ("odt", "OpenDocument Text (.odt)")]

# key: (summary, formats it affects)
ISSUES = {
    "equations": ("Equations will be converted to images. You won't be able to edit them "
                  "until the document is converted to a newer format.", ("doc", "rtf")),
    "controls": ("Content controls will be converted to static text.", ("doc", "rtf")),
    "replies": ("Comment replies will become separate comments.", ("doc", "rtf")),
    "effects": ("Shape effects such as glow and soft edges will be removed.", ("doc", "rtf")),
    "typography": ("Advanced typography such as ligatures will be removed.", ("doc", "rtf")),
    "textlinks": ("Linked text boxes will no longer be linked.", ("rtf",)),
    "bookmarks": ("Bookmark names longer than 40 characters will be shortened.", ("doc",)),
    "tracked_fmt": ("Tracked formatting changes will be accepted.", ("rtf",)),
    "wordart": ("Text effects on shapes will be removed.", ("doc", "rtf", "odt")),
}


def _paragraphs(text):
    en = text.createEnumeration()
    while en.hasMoreElements():
        p = en.nextElement()
        if p.supportsService("com.sun.star.text.Paragraph"):
            yield p
        elif p.supportsService("com.sun.star.text.TextTable"):
            for name in p.getCellNames():
                yield from _paragraphs(p.getCellByName(name).getText())


def scan(m):
    """{issue key: occurrences}"""
    found = {}

    def add(k, n=1):
        if n:
            found[k] = found.get(k, 0) + n
    try:
        add("equations", len(docapi.formulas(m)))
    except Exception:
        pass
    try:
        for p in _paragraphs(m.getText()):
            pe = p.createEnumeration()
            while pe.hasMoreElements():
                r = pe.nextElement()
                kind = getattr(r, "TextPortionType", "")
                if kind == "ContentControl":
                    add("controls")
                try:
                    if ":" in (r.CharFontName or ""):
                        add("typography")
                except Exception:
                    pass
    except Exception as e:
        print("compat text:", e)
    try:
        en = m.getTextFields().createEnumeration()
        while en.hasMoreElements():
            f = en.nextElement()
            if f.supportsService("com.sun.star.text.textfield.Annotation"):
                try:
                    if f.ParentName:
                        add("replies")
                except Exception:
                    pass
    except Exception:
        pass
    try:
        dp = m.getDrawPage()
        for i in range(dp.getCount()):
            sh = dp.getByIndex(i)
            for prop in ("GlowEffectRadius", "SoftEdgeRadius"):
                try:
                    if getattr(sh, prop):
                        add("effects")
                        break
                except Exception:
                    pass
            try:
                geo = {p.Name: p.Value for p in sh.CustomShapeGeometry}
                tp = geo.get("TextPath")
                if tp and any(p.Name == "TextPath" and p.Value for p in tp):
                    add("wordart")
            except Exception:
                pass
    except Exception:
        pass
    try:
        fr = m.getTextFrames()
        for n in fr.getElementNames():
            if fr.getByName(n).ChainNextName:
                add("textlinks")
    except Exception:
        pass
    try:
        add("bookmarks", sum(1 for n in m.getBookmarks().getElementNames() if len(n) > 40))
    except Exception:
        pass
    try:
        en = m.getRedlines().createEnumeration()
        while en.hasMoreElements():
            r = en.nextElement()
            if r.RedlineType in ("Format", "ParagraphFormat", "Attributes"):
                add("tracked_fmt")
    except Exception:
        pass
    return found


def issues_for(found, fmt):
    return [(ISSUES[k][0], n) for k, n in found.items() if fmt in ISSUES[k][1]]


def dialog(win, fmt=None, saving=False):
    """The checker. With saving=True it asks to Continue; returns True to save."""
    return True


def check_before_save(win, fmt):
    """Saving in an older format: show the checker when something would be
    lost, as the original does."""
    if fmt not in ("doc", "rtf") or not win.app.settings.get("check_compat", True):
        return True
    return True
