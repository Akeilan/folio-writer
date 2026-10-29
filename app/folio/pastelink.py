"""Paste Special > Paste link: text copied from a saved document is pasted as
a LINK field pointing at a bookmark of the copied text in the source, and
updates from it (F9, or right-click Update Link), as in the original."""

SOURCE = {}


def remember_copy(win, text):
    """Called on Copy: keep where the copied text is, so it can be linked to."""
    SOURCE.clear()
    ed = win.engine.ed
    if ed is None or not text or ed.story() != "body":
        return
    SOURCE.update(win=win, text=text, range=tuple(ed.selection_range()))


def available(win, clip_text):
    """Can the clipboard be pasted as a link?"""
    src = SOURCE.get("win")
    return bool(src is not None and src is not win and SOURCE.get("text") and
                (clip_text or "").strip() == SOURCE["text"].strip())


def paste(win):
    src = SOURCE.get("win")
    if src is None:
        return False
    if not src.engine.path:
        win.dialogs.message("Save the document you copied from first, then paste the "
                            "link again.")
        return False
    sed = src.engine.ed
    names = set(sed.all_bookmark_names())
    n = 1
    while "OLE_LINK%d" % n in names:
        n += 1
    name = "OLE_LINK%d" % n
    keep = tuple(sed.selection_range())
    pa, a, pb, b = SOURCE["range"]
    if not sed.select_nodes(pa, a, pb, b) or not sed.add_bookmark(name):
        win.dialogs.message("The text you copied has changed in its document. Copy it again, "
                            "then paste the link.")
        sed.select_nodes(*keep)
        return False
    sed.select_nodes(*keep)
    src.engine.view.document_changed()
    if not src.engine.save():
        return False
    path = src.engine.path.replace("\\", "\\\\").replace('"', "")
    ed = win.engine.ed
    ed.begin_group("Paste Link")
    try:
        ed.insert_field('LINK Word.Document.12 "%s" "%s" \\a \\t' % (path, name), SOURCE["text"])
    finally:
        ed.end_group()
    win.engine.view.after_edit()
    return True


def at_caret(win):
    """Is the caret in a pasted link?"""
    ed = win.engine.ed
    return ed is not None and ed.field_at_caret("LINK") is not None


def update(win):
    """Update Link: the links in the selection (all of them if there is none)."""
    ed = win.engine.ed
    ed.update_fields(not ed.has_selection() and not at_caret(win))
    win.engine.view.after_edit()
