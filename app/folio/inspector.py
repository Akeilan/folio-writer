"""Document Inspector (File > Info > Check for Issues > Inspect Document):
find and remove comments, revisions, personal information, headers and
footers, hidden text and invisible objects."""
from gi.repository import Gtk

from .widgets import FDialog

CATEGORIES = [
    ("comments", "Comments, Revisions, and Versions",
     "Inspects the document for comments, versions, and revision marks."),
    ("props", "Document Properties and Personal Information",
     "Inspects for hidden metadata or personal information saved with the document."),
    ("hf", "Headers, Footers, and Watermarks",
     "Inspects the document for information in headers, footers, and watermarks."),
    ("hidden", "Hidden Text", "Inspects the document for text that has been formatted as "
     "hidden."),
    ("invisible", "Invisible Content", "Inspects the document for objects that are not "
     "visible because they have been formatted as invisible."),
]


def inspect(win, key):
    """(found, message)"""
    ed = win.engine.ed
    c = ed.inspect_counts()
    if key == "comments":
        bits = []
        if c.get("comments"):
            bits.append("Comments")
        if c.get("revisions"):
            bits.append("Revision marks")
        return bool(bits), ("The following items were found:\n\u2022 " + "\n\u2022 ".join(bits)
                            if bits else "No comments or revisions were found.")
    if key == "props":
        from .native import docprops
        d = docprops.core(ed)
        bits = []
        if (d.get("creator") or "").strip() or (d.get("lastModifiedBy") or "").strip():
            bits.append("Author")
        if any((d.get(k) or "").strip() for k in ("title", "subject", "keywords", "description",
                                                   "category")):
            bits.append("Document properties")
        if docprops.custom(ed):
            bits.append("Custom properties")
        return bool(bits), ("The following document information was found:\n\u2022 " +
                            "\n\u2022 ".join(bits) if bits else
                            "No document properties or personal information was found.")
    if key == "hf":
        bits = (["Headers", "Footers"] if c.get("hf") else []) + (["Watermarks"] if c.get("watermark") else [])
        return bool(bits), ("The following items were found:\n\u2022 " + "\n\u2022 ".join(bits)
                            if bits else "No custom header, footer, or watermark information was found.")
    if key == "hidden":
        n = c.get("hidden", 0)
        return bool(n), ("Hidden text was found." if n else "No hidden text was found.")
    if key == "invisible":
        n = c.get("invisible", 0)
        return bool(n), ("Invisible objects found: %d" % n if n else "No invisible objects found.")
    return False, ""


def remove(win, key):
    ed = win.engine.ed
    ed.begin_group("Remove All")
    try:
        if key == "comments":
            ed.delete_all_comments(None)
            ed.accept_reject_all(True, None)
        elif key == "props":
            from .native import docprops
            docprops.set_core(ed, creator="", lastModifiedBy="", title="", subject="",
                              keywords="", description="", category="", lastPrinted="")
            for name in list(docprops.custom(ed)):
                if not name.startswith("Folio"):
                    docprops.set_custom(ed, name, None)
            ed.set_setting("removePersonalInformation", True)
        else:
            ed.inspect_remove(key)
    finally:
        ed.end_group()
    win.engine.view.document_changed()


def dialog(win):
    if win.engine.modified and win.dialogs.confirm(
            "This document has changes that haven't been saved. Do you want to save the "
            "file now?", yes="Yes", no="No"):
        win.save()
    d = FDialog(win, "Document Inspector", buttons=(("Inspect", 10),
                                                    ("Close", Gtk.ResponseType.CANCEL)))
    d.set_default_size(560, -1)
    intro = Gtk.Label(label="To check the document for the selected content, click "
                            "Inspect.", xalign=0)
    d.add(intro)
    stack = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    sw = Gtk.ScrolledWindow()
    sw.set_size_request(540, 340)
    sw.add(stack)
    d.add(sw, expand=True)
    checks = {}

    def show_checks():
        for c in stack.get_children():
            stack.remove(c)
        for key, title, desc in CATEGORIES:
            cb = Gtk.CheckButton()
            lab = Gtk.Label(xalign=0)
            lab.set_markup("<b>%s</b>\n<small>%s</small>" % (title, desc))
            lab.set_line_wrap(True)
            cb.add(lab)
            cb.set_active(checks.get(key, True) if not isinstance(checks.get(key), Gtk.Widget)
                          else checks[key].get_active())
            checks[key] = cb
            stack.pack_start(cb, False, False, 0)
        stack.show_all()

    def show_results():
        sel = [k for k, cb in checks.items() if cb.get_active()]
        for c in stack.get_children():
            stack.remove(c)
        intro.set_text("Review the inspection results.")
        for key, title, _desc in CATEGORIES:
            if key not in sel:
                continue
            found, msg = inspect(win, key)
            row = Gtk.Box(spacing=10)
            icon = Gtk.Image.new_from_icon_name("dialog-warning-symbolic" if found else
                                                "emblem-ok-symbolic", Gtk.IconSize.LARGE_TOOLBAR)
            row.pack_start(icon, False, False, 0)
            lab = Gtk.Label(xalign=0)
            lab.set_markup("<b>%s</b>\n<small>%s</small>" % (
                title, msg.replace("&", "&amp;")))
            lab.set_line_wrap(True)
            lab.set_max_width_chars(48)
            row.pack_start(lab, True, True, 0)
            if found:
                b = Gtk.Button(label="Remove All")

                def go(_b, key=key, icon=icon, lab=lab, title=title):
                    remove(win, key)
                    _b.hide()
                    icon.set_from_icon_name("emblem-ok-symbolic", Gtk.IconSize.LARGE_TOOLBAR)
                    lab.set_markup("<b>%s</b>\n<small>Removed.</small>" % title)
                b.connect("clicked", go)
                b.set_valign(Gtk.Align.CENTER)
                row.pack_start(b, False, False, 0)
            stack.pack_start(row, False, False, 0)
            stack.pack_start(Gtk.Separator(), False, False, 0)
        stack.show_all()
        d.buttons[10].set_label("Reinspect")
    show_checks()
    while True:
        r = d.ask()
        if r == 10:
            if d.buttons[10].get_label() == "Reinspect":
                d.buttons[10].set_label("Inspect")
                intro.set_text("To check the document for the selected content, click "
                               "Inspect.")
                show_checks()
            else:
                show_results()
            continue
        break
    d.done()
