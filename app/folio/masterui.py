"""Outlining > Master Document (W3-07): the buttons' actions."""
from .native import masterdoc as M


def _ed(win):
    return getattr(win.engine, "ed", None)


def _refresh(win):
    win.engine.view.after_edit()
    v = win.outline()
    if v is not None:
        v.load()
    update(win)


def _need_saved(win, what):
    if win.engine.path is None or win.engine.is_new:
        win.dialogs.message("Save the master document before you %s." % what)
        return False
    return True


def update(win):
    """The group's buttons as Word shows them: the editing ones after Show Document."""
    btns = getattr(win, "master_buttons", None)
    if not btns:
        return
    shown = getattr(win, "master_shown", False)
    for key, b in btns.items():
        if key in ("show", "collapse"):
            continue
        b.set_no_show_all(True)
        b.set_visible(shown)
    ed = _ed(win)
    subs = M.subdocs(ed) if ed is not None else []
    col = btns.get("collapse")
    if col is not None:
        expanded = any(e for _n, e, _p in subs) or not subs
        col.set_label_text("Collapse\nSubdocuments" if expanded else "Expand\nSubdocuments")
        col.set_sensitive(bool(subs))
    for key, on in (("show", shown), ("lock", bool(getattr(win, "master_locked", False)))):
        b = btns.get(key)
        if b is not None:
            b.apply_state("true" if on else "false")


def show_document(win):
    win.master_shown = not getattr(win, "master_shown", False)
    update(win)


def create(win):
    ed = _ed(win)
    v = win.outline()
    start = None
    if v is not None:
        p = v._selected_para()
        start = p.node if p is not None else None
    if not M.create(ed, start):
        win.dialogs.message("Select a heading (or text) that isn't part of a subdocument to create one.")
        return
    _refresh(win)


def insert(win):
    path = win.dialogs.pick_file("Insert Subdocument", ["*.docx", "*.docm", "*.doc", "*.rtf", "*.odt"],
                                 "Documents")
    if not path:
        return
    if not path.lower().endswith((".docx", ".docm")):
        win.dialogs.message("A subdocument is a Word Document (.docx). Open this file and save it as a "
                            "Word Document first.")
        return
    if M.insert(_ed(win), path, win.engine.path) is None:
        win.dialogs.message("That document couldn't be inserted.")
        return
    _refresh(win)


def unlink(win):
    if not M.unlink(_ed(win)):
        win.dialogs.message("Put the cursor in an expanded subdocument to unlink it.")
        return
    _refresh(win)


def merge(win):
    if not M.merge(_ed(win)):
        win.dialogs.message("Select two or more subdocuments that follow each other to merge them.")
        return
    _refresh(win)


def split(win):
    if not M.split(_ed(win)):
        win.dialogs.message("Put the cursor at the paragraph where the subdocument should split "
                            "(not its first paragraph).")
        return
    _refresh(win)


def collapse_expand(win):
    ed = _ed(win)
    subs = M.subdocs(ed)
    if not subs:
        return
    if any(e for _n, e, _p in subs):
        if not _need_saved(win, "collapse its subdocuments"):
            return
        M.collapse(ed, win.engine.path)
    else:
        if not M.expand(ed, win.engine.path):
            win.dialogs.message("The subdocuments' files couldn't be found.")
    _refresh(win)


def lock(win):
    win.master_locked = not getattr(win, "master_locked", False)
    win.read_only = win.master_locked
    try:
        win.engine.view.set_edit(not win.master_locked)
    except Exception:
        pass
    win.update_title()
    update(win)
