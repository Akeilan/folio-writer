"""File > Info > Check for Issues > Check Compatibility: features of this
document that are lost or changed when it is saved in an older or other
file format."""
from gi.repository import Gtk

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


def scan(win):
    """{issue key: occurrences}"""
    return {k: n for k, n in win.engine.ed.inspect_counts().items() if k in ISSUES and n}


def issues_for(found, fmt):
    return [(ISSUES[k][0], n) for k, n in found.items() if fmt in ISSUES[k][1]]


def dialog(win, fmt=None, saving=False):
    """The checker. With saving=True it asks to Continue; returns True to save."""
    if win.engine.ed is None:
        return True
    found = scan(win)
    buttons = (("Continue", 10), ("Cancel", Gtk.ResponseType.CANCEL)) if saving else \
        (("OK", Gtk.ResponseType.OK),)
    d = FDialog(win, "Compatibility Checker", buttons=buttons)
    d.set_default_size(560, -1)
    d.add(Gtk.Label(label="Compatibility report for %s" % win.doc_name(), xalign=0))
    row = Gtk.Box(spacing=8)
    row.pack_start(Gtk.Label(label="Select formats to show:"), False, False, 0)
    pick = Gtk.ComboBoxText()
    for k, lab in TARGETS:
        pick.append(k, lab)
    pick.set_active_id(fmt if fmt in dict(TARGETS) else "doc")
    pick.set_sensitive(not saving)
    row.pack_start(pick, False, False, 0)
    d.add(row)
    d.add(Gtk.Label(label="The following features in this document are not supported in the "
                          "selected format. They may be lost or permanently changed when you "
                          "save the document in it.", xalign=0, wrap=True, max_width_chars=70))
    store = Gtk.ListStore(str, str)
    tv = Gtk.TreeView(model=store)
    for i, (title, expand) in enumerate((("Summary", True), ("Occurrences", False))):
        cell = Gtk.CellRendererText()
        if i == 0:
            cell.set_property("wrap-width", 420)
            cell.set_property("wrap-mode", 2)
        else:
            cell.set_property("xalign", 0.5)
        col = Gtk.TreeViewColumn(title, cell, text=i)
        col.set_expand(expand)
        tv.append_column(col)
    sw = Gtk.ScrolledWindow()
    sw.set_size_request(540, 220)
    sw.add(tv)
    d.add(sw, expand=True)

    def fill(*_):
        store.clear()
        rows = issues_for(found, pick.get_active_id())
        if not rows:
            store.append(["No compatibility issues were found.", ""])
        for text, n in rows:
            store.append([text, str(n)])
    pick.connect("changed", fill)
    fill()
    chk = Gtk.CheckButton(label="Check compatibility when saving documents")
    chk.set_active(win.app.settings.get("check_compat", True))
    d.add(chk)
    r = d.ask()
    win.app.settings["check_compat"] = chk.get_active()
    win.app.save_settings()
    d.done()
    return r in (10, Gtk.ResponseType.OK)


def check_before_save(win, fmt):
    """Saving in an older format: show the checker when something would be
    lost, as the original does."""
    if fmt not in ("doc", "rtf") or not win.app.settings.get("check_compat", True):
        return True
    if win.engine.ed is None or not issues_for(scan(win), fmt):
        return True
    return dialog(win, fmt, saving=True)
