"""Backstage > Info extras: Mark as Final, the message bar, and version history (W4-02):
every save is kept on this computer, listed with its date, and can be opened, compared with
what is there now, or restored. AutoRecover snapshots are kept the same way, and marked as
such. Nothing leaves the machine; Word's own version history is cloud-only."""
import hashlib
import os
import shutil
import time

from gi.repository import GLib, Gtk

from . import modelapi


# ------------------------------------------------------------ message bar
class MessageBar(Gtk.Box):
    """The yellow bar under the ribbon (Marked as Final, autosaved versions)."""

    def __init__(self, win):
        Gtk.Box.__init__(self, spacing=10)
        self.win = win
        self.get_style_context().add_class("folio-msgbar")
        self.set_no_show_all(True)
        self.icon = Gtk.Image.new_from_icon_name("dialog-information-symbolic",
                                                 Gtk.IconSize.MENU)
        self.title = Gtk.Label(xalign=0)
        self.text = Gtk.Label(xalign=0)
        self.text.set_ellipsize(3)
        self.buttons = Gtk.Box(spacing=6)
        close = Gtk.Button()
        close.set_relief(Gtk.ReliefStyle.NONE)
        close.add(Gtk.Image.new_from_icon_name("window-close-symbolic", Gtk.IconSize.MENU))
        close.connect("clicked", lambda *_: self.hide_bar())
        for w in (self.icon, self.title, self.text):
            self.pack_start(w, False, False, 0)
        self.pack_start(self.buttons, False, False, 8)
        self.pack_end(close, False, False, 0)
        self.kind = None

    def show_bar(self, kind, title, text, buttons=()):
        self.kind = kind
        self.title.set_markup("<b>%s</b>" % title)
        self.text.set_text(text)
        for c in self.buttons.get_children():
            self.buttons.remove(c)
        for label, cb in buttons:
            b = Gtk.Button(label=label)
            b.connect("clicked", lambda _b, cb=cb: cb())
            self.buttons.pack_start(b, False, False, 0)
        for w in self.get_children() + self.buttons.get_children():
            w.show_all()
        self.show()

    def hide_bar(self, kind=None):
        if kind is None or kind == self.kind:
            self.hide()
            self.kind = None


# ------------------------------------------------------------ mark as final
def is_final(m):
    # Word's _MarkAsFinal custom property (older Folio files: MarkedFinal)
    v = modelapi._doc_setting(m, "_MarkAsFinal", None)
    if v is not None:
        return v is True or str(v).lower() in ("true", "1")
    return modelapi._doc_setting(m, "MarkedFinal", "") == "1"


def _set_final(m, on):
    try:
        ud = m.getDocumentProperties().getUserDefinedProperties()
        if ud.getPropertySetInfo().hasPropertyByName("MarkedFinal"):
            ud.removeProperty("MarkedFinal")
        if on:
            modelapi._set_doc_setting(m, "_MarkAsFinal", True)
        elif ud.getPropertySetInfo().hasPropertyByName("_MarkAsFinal"):
            ud.removeProperty("_MarkAsFinal")
    except Exception:
        modelapi._set_doc_setting(m, "MarkedFinal", "1" if on else "")
    try:
        p = m.getDocumentProperties()
        if on:
            p.ContentStatus = "Final"
        elif getattr(p, "ContentStatus", "") == "Final":
            p.ContentStatus = ""
    except Exception:
        pass


def mark_final(win, on=True):
    m = win.docmodel
    if m is None:
        return
    if on:
        if not win.dialogs.confirm("This document will be marked as final and then saved.",
                                   yes="OK", no="Cancel"):
            return
        _set_final(m, True)
        if win.save():
            win.dialogs.message(
                "This document has been marked as final to indicate that editing is "
                "complete and that this is the final version of the document.\n\n"
                "When a document is marked as final, the status property is set to "
                "“Final” and typing, editing commands, and proofing marks are "
                "turned off.", title="Marked as Final")
        apply_final(win)
    else:
        _set_final(m, False)
        apply_final(win)


def apply_final(win):
    m = win.docmodel
    if m is None:
        return
    if is_final(m):
        win.read_only = True
        win.engine.view.set_edit(False)
        win.msgbar.show_bar("final", "MARKED AS FINAL",
                            "An author has marked this document as final to discourage "
                            "editing.", [("Edit Anyway", lambda: edit_anyway(win))])
    else:
        if win.msgbar.kind == "final":
            win.read_only = False
            win.engine.view.set_edit(True)
            win.msgbar.hide_bar("final")
    win.update_title()


def edit_anyway(win):
    m = win.docmodel
    if m is not None:
        _set_final(m, False)
    win.read_only = False
    win.engine.view.set_edit(True)
    win.msgbar.hide_bar("final")
    win.update_title()


# ------------------------------------------------------------ versions
KEEP = 25                 # versions of one document before the oldest is dropped
VERSION_EXT = (".odt", ".docx", ".docm", ".dotx", ".doc", ".dot", ".rtf")


def versions_dir(app, path):
    key = hashlib.sha1(os.path.abspath(path).encode()).hexdigest()[:16]
    return os.path.join(app.autorecover_dir, "versions", key)


def wanted(app):
    """Whether versions are being kept at all, and how many."""
    s = getattr(app, "settings", {}) or {}
    return bool(s.get("versions", True)), max(1, min(200, int(s.get("versions_keep", KEEP) or KEEP)))


def _trim(d, keep):
    """Drop the oldest until only `keep` are left."""
    got = []
    for f in os.listdir(d):
        p = _parse(f)
        if p:
            got.append((p[0], f))
    got.sort(reverse=True)
    for _when, f in got[keep:]:
        try:
            os.remove(os.path.join(d, f))
        except OSError:
            pass


def _parse(name):
    """A version file name -> (when in seconds, "save" or "autosave").

    New names are '<milliseconds>-save.docx' — milliseconds, so two saves in the same second each
    keep their own version. Names left by earlier releases are a plain '<seconds>.odt'."""
    stem, ext = os.path.splitext(name)
    if ext not in VERSION_EXT:
        return None
    when, sep, kind = stem.partition("-")
    try:
        n = int(when)
    except ValueError:
        return None
    if not sep:
        return n, "autosave"                       # written before W4-02
    return n // 1000, (kind if kind in ("save", "autosave") else "autosave")


def keep_saved_copy(app, path):
    """Keep the document as it is on disk now, before a save writes over it (W4-02). Returns the
    version's path, or None if there was nothing to keep."""
    on, keep = wanted(app)
    if not on or not path or not os.path.isfile(path):
        return None
    ext = os.path.splitext(path)[1].lower()
    if ext not in VERSION_EXT:
        return None
    d = versions_dir(app, path)
    os.makedirs(d, exist_ok=True)
    try:
        ms = os.stat(path).st_mtime_ns // 1000000
    except OSError:
        ms = int(time.time() * 1000)
    target = os.path.join(d, "%d-save%s" % (ms, ext))
    if os.path.exists(target):
        return target                   # this very save is already kept
    try:
        shutil.copy2(path, target)
    except OSError:
        return None
    _trim(d, keep)
    return target


def keep_version(app, win, keep=None):
    """Store an AutoRecover snapshot of a saved document as a version."""
    on, limit = wanted(app)
    if not on:
        return None
    keep = keep or limit
    path = win.engine.path
    if not path or win.engine.is_new:
        return None
    d = versions_dir(app, path)
    os.makedirs(d, exist_ok=True)
    target = os.path.join(d, "%d-autosave.odt" % int(time.time() * 1000))
    if not win.engine.save_as(target, "odt", keep=False):
        return None
    _trim(d, keep)
    return target


def versions(app, path):
    """[(when, file, "save" or "autosave")], newest first."""
    if not path:
        return []
    d = versions_dir(app, path)
    if not os.path.isdir(d):
        return []
    out = []
    for f in os.listdir(d):
        got = _parse(f)
        if got:
            out.append((got[0], os.path.join(d, f), got[1]))
    out.sort(key=lambda v: v[0], reverse=True)
    return out


def forget_versions(app, path):
    """Throw this document's kept versions away. Returns how many went."""
    d = versions_dir(app, path) if path else None
    if not d or not os.path.isdir(d):
        return 0
    n = len(versions(app, path))
    shutil.rmtree(d, ignore_errors=True)
    return n


def version_label(ts, kind="autosave"):
    import datetime
    t = datetime.datetime.fromtimestamp(ts)
    today = datetime.date.today()
    if t.date() == today:
        day = "Today"
    elif (today - t.date()).days == 1:
        day = "Yesterday"
    else:
        day = t.strftime("%A, %B %-d")
    return "%s, %s (%s)" % (day, t.strftime("%-I:%M %p"), "saved" if kind == "save" else "autosave")


def open_version(win, ts, vpath, kind="autosave"):
    """Open a kept version in its own window, read-only, with Restore / Compare."""
    original = win.engine.path
    w = win.app.new_window(template=vpath)
    label = version_label(ts, kind)
    w.untitled = "%s (%s)" % (win.doc_name(), label.split(" (")[0])

    def restore():
        if not win.dialogs.confirm("You are about to overwrite the last saved version with "
                                   "the selected version.", yes="OK", no="Cancel"):
            return
        fmt = os.path.splitext(original)[1].lstrip(".").lower() or "docx"
        if w.engine.save_as(original, fmt, keep=False):
            w.engine.mark_saved()
            w.close_document()
            for other in win.app.windows:
                if other.engine.path == original:
                    other.open_file(original)
        else:
            w.dialogs.message("The version couldn't be restored.")

    def compare():
        from .native import compare as C
        w.read_only = False
        w.engine.view.set_edit(True)
        if not C.compare(w, original, win.app.user_name() or "Author"):
            w.dialogs.message("This version and the saved document are the same.")
        w.engine.view.set_edit(False)
        w.read_only = True

    def ready():
        w.read_only = True
        w.engine.view.set_edit(False)
        w.update_title()
        w.msgbar.show_bar("version", "SAVED VERSION" if kind == "save" else "AUTOSAVED VERSION",
                          "This is how the document stood on %s. It is kept on this computer."
                          % label.split(" (")[0] if kind == "save" else
                          "This is a temporary file that was saved automatically.",
                          [("Compare", compare), ("Restore", restore)])
        return False
    from gi.repository import GLib
    GLib.timeout_add(900, ready)
    return w


def history_dialog(win):
    """Version History (W4-02): every version of this document kept on this computer, with the
    date it was kept, and what can be done with it."""
    app, eng = win.app, win.engine
    if not eng.path or eng.is_new:
        win.dialogs.message("Save the document first; versions are kept from then on.")
        return None
    from .widgets import FDialog
    d = FDialog(win, "Version History", buttons=(("Close", Gtk.ResponseType.CLOSE),), width=560)
    d.set_resizable(True)
    head = Gtk.Label(xalign=0)
    d.box.pack_start(head, False, False, 0)
    sw = Gtk.ScrolledWindow()
    sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    sw.set_size_request(-1, 280)
    lb = Gtk.ListBox()
    lb.set_selection_mode(Gtk.SelectionMode.SINGLE)
    sw.add(lb)
    d.box.pack_start(sw, True, True, 0)
    foot = Gtk.Box(spacing=6)
    d.box.pack_start(foot, False, False, 0)
    d.rows = []
    actions = {}

    def selected():
        r = lb.get_selected_row()
        return getattr(r, "version", None)

    def fill():
        for child in lb.get_children():
            lb.remove(child)
        d.rows = []
        vers = versions(app, eng.path)
        on, keep = wanted(app)
        if not vers:
            head.set_markup("<b>No versions yet.</b>\nA version is kept each time the document is "
                            "saved%s." % ("" if on else ", once version history is turned back on in "
                                         "Options \u203a Save"))
        else:
            head.set_markup("<b>%d version%s of %s</b>\nKept on this computer, newest first. The "
                            "oldest goes when there are more than %d."
                            % (len(vers), "" if len(vers) == 1 else "s",
                               GLib.markup_escape_text(os.path.basename(eng.path)), keep))
        for ts, vp, kind in vers:
            row = Gtk.ListBoxRow()
            row.version = (ts, vp, kind)
            bx = Gtk.Box(spacing=10)
            bx.set_border_width(6)
            lab = Gtk.Label(xalign=0)
            try:
                size = "%dKB" % max(1, os.path.getsize(vp) // 1024)
            except OSError:
                size = ""
            lab.set_markup("<b>%s</b>\n<small>%s</small>"
                           % (GLib.markup_escape_text(version_label(ts, kind)),
                              GLib.markup_escape_text(" \u00b7 ".join(x for x in (size, os.path.basename(vp)) if x))))
            bx.pack_start(lab, True, True, 0)
            row.add(bx)
            lb.add(row)
            d.rows.append(row)
        lb.show_all()
        if d.rows:
            lb.select_row(d.rows[0])
        for b in actions.values():
            b.set_sensitive(bool(d.rows))

    def do_open():
        v = selected()
        if v:
            d.response(Gtk.ResponseType.CLOSE)
            open_version(win, v[0], v[1], v[2])

    def do_restore():
        v = selected()
        if not v:
            return
        d.response(Gtk.ResponseType.CLOSE)
        open_version(win, v[0], v[1], v[2])

    def do_delete():
        v = selected()
        if not v or not win.dialogs.confirm(
                "Delete the version from %s? This cannot be undone." % version_label(v[0], v[2]).split(" (")[0],
                yes="Delete", no="Cancel"):
            return
        try:
            os.remove(v[1])
        except OSError:
            win.dialogs.message("That version couldn\u2019t be deleted.")
        fill()

    def do_clear():
        if not win.dialogs.confirm("Delete every kept version of this document? This cannot be undone.",
                                   yes="Delete All", no="Cancel"):
            return
        forget_versions(app, eng.path)
        fill()

    def do_folder():
        import subprocess
        dd = versions_dir(app, eng.path)
        os.makedirs(dd, exist_ok=True)
        subprocess.Popen(["xdg-open", dd])

    for label, cb, key in (("Open", do_open, "open"), ("Restore", do_restore, "restore"),
                           ("Delete", do_delete, "delete"), ("Delete All", do_clear, "clear")):
        b = Gtk.Button(label=label)
        b.connect("clicked", lambda _b, cb=cb: cb())
        actions[key] = b
        foot.pack_start(b, False, False, 0)
    where = Gtk.Button(label="Open Folder")
    where.connect("clicked", lambda *_: do_folder())
    foot.pack_end(where, False, False, 0)
    lb.connect("row-activated", lambda *_: do_open())
    d.actions = actions
    d.fill = fill
    fill()
    d.show_all()
    win.version_history = d
    try:
        d.run()
    finally:
        win.version_history = None
        d.destroy()
    return d


def recover_unsaved(win):
    files = win.app.recovered_files()
    if not files:
        win.dialogs.message("There are no unsaved documents to recover.")
        return
    from .widgets import FDialog
    d = FDialog(win, "Recover Unsaved Documents", buttons=(("Open", Gtk.ResponseType.OK),
                                                           ("Cancel",
                                                            Gtk.ResponseType.CANCEL)))
    lb = Gtk.ListBox()
    for p, info in files:
        row = Gtk.ListBoxRow()
        row.path = p
        try:
            when = time.strftime("%-m/%-d/%Y %-I:%M %p", time.localtime(os.path.getmtime(p)))
        except OSError:
            when = ""
        lab = Gtk.Label(xalign=0)
        lab.set_markup("<b>%s</b>   <small>%s</small>" % (
            (info.get("name") or os.path.basename(p)).replace("&", "&amp;"), when))
        lab.set_margin_top(4)
        lab.set_margin_bottom(4)
        row.add(lab)
        lb.add(row)
    lb.select_row(lb.get_row_at_index(0))
    lb.connect("row-activated", lambda *_: d.response(Gtk.ResponseType.OK))
    d.add(lb)
    r = d.ask()
    row = lb.get_selected_row()
    d.done()
    if r == Gtk.ResponseType.OK and row is not None:
        w = win.app.new_window(template=row.path)
        try:
            dest = os.path.join(os.path.dirname(row.path), "recovered")
            os.makedirs(dest, exist_ok=True)
            shutil.move(row.path, os.path.join(dest, os.path.basename(row.path)))
            os.remove(row.path + ".info")
        except OSError:
            pass
        return w
