"""Editing conveniences from the original:

* Collapse / expand headings: a small triangle beside a heading (shown when
  the mouse is over it, and always for collapsed headings) folds away
  everything up to the next heading of the same or a higher level. It is a
  view setting: nothing is hidden in the file. Headings marked "Collapsed by
  default" (Paragraph dialog) open collapsed.
* The Spike: Ctrl+F3 cuts the selection onto the Spike, Ctrl+Shift+F3
  pastes everything on it and empties it.
* Resume reading: "Welcome back! Pick up where you left off" on reopening.
"""
import time

from gi.repository import Gdk, GLib, Gtk

TRI = 11            # triangle size (px)


# ============================================================ headings
class HeadingFolds:
    def __init__(self, win):
        self.win = win
        self.hover = None
        view = win.engine.view
        view.connect_after("draw", self._draw)
        view.connect("motion-notify-event", self._motion)

    @property
    def ed(self):
        return self.win.engine.ed

    def _enabled(self):
        return self.win.app.settings.get("collapse_headings", True) and self.ed is not None \
            and self.ed.view_mode() == 0 and self.ed.story() == "body"

    def marks(self):
        try:
            return self.ed.heading_marks()
        except Exception:
            return []

    def _tri_rect(self, mk):
        _node, _lvl, pg, x, y, h, _f = mk
        v = self.win.engine.view
        wx, wy = v.to_widget(pg, x, y)
        hh = h * v.ppp
        return wx - TRI - 8, wy + hh / 2 - TRI / 2, TRI + 6, TRI

    def _mark_at(self, x, y, band=False):
        v = self.win.engine.view
        for mk in self.marks():
            rx, ry, rw, rh = self._tri_rect(mk)
            if band:
                _wx, wy = v.to_widget(mk[2], mk[3], mk[4])
                if wy - 2 <= y <= wy + mk[5] * v.ppp + 2:
                    return mk
            elif rx - 3 <= x <= rx + rw + 3 and ry - 4 <= y <= ry + rh + 4:
                return mk
        return None

    def _motion(self, view, event):
        if not self._enabled():
            return False
        mk = self._mark_at(event.x, event.y, band=True)
        key = mk[0] if mk else None
        if key != self.hover:
            self.hover = key
            view.queue_draw()
        return False

    def press(self, event):
        """A click on a triangle (from the window's press hook)."""
        if event.button != 1 or event.type != Gdk.EventType.BUTTON_PRESS or not self._enabled():
            return False
        mk = self._mark_at(event.x, event.y)
        if mk is None:
            return False
        self.toggle(mk[0])
        return True

    def toggle(self, node):
        if self.ed.toggle_fold(node):
            self.win.engine.view.document_changed()

    def is_collapsed(self, node):
        return self.ed.is_folded(node)

    def expand_all(self):
        self.ed.fold_all(False)
        self.win.engine.view.document_changed()

    def collapse_all(self):
        self.ed.fold_all(True)
        self.win.engine.view.document_changed()

    def apply_defaults(self):
        if self.ed is not None and self.ed.fold_defaults():
            self.win.engine.view.document_changed()
        return False

    def _draw(self, view, cr):
        if not self._enabled():
            return False
        for mk in self.marks():
            col = mk[6]
            if not col and mk[0] != self.hover:
                continue
            x, y, w, h = self._tri_rect(mk)
            cr.save()
            cr.set_source_rgb(0.35, 0.35, 0.35)
            if col:         # pointing right: collapsed
                cr.move_to(x + 3, y)
                cr.line_to(x + 3 + h * 0.8, y + h / 2)
                cr.line_to(x + 3, y + h)
            else:           # pointing down-right: expanded
                cr.move_to(x + 3 + h, y)
                cr.line_to(x + 3 + h, y + h)
                cr.line_to(x + 3, y + h)
            cr.close_path()
            cr.fill()
            cr.restore()
        return False


def caret_heading(win):
    """(node, level) of the heading the caret is in, or (None, 0)."""
    ed = win.engine.ed
    if ed is None or ed.story() != "body":
        return None, 0
    node = ed.caret_pos()[0]
    for n, _t, lvl, *_r in ed.outline_paras():
        if n == node:
            return (n, lvl) if lvl <= 9 else (None, 0)
    return None, 0


def is_collapsed_by_default(win):
    node, _lvl = caret_heading(win)
    return node is not None and win.engine.ed.collapsed_default(node)


def set_collapsed_by_default(win, on):
    node, _lvl = caret_heading(win)
    if node is None:
        return
    ed = win.engine.ed
    ed.set_collapsed_default(node, bool(on))
    if bool(on) != ed.is_folded(node):
        ed.toggle_fold(node)
    win.engine.view.document_changed()


# ============================================================ spike
def spike_cut(win):
    win.run("spike")


def spike_paste(win):
    win.run("spike-paste")


# ============================================================ resume reading
def remember_position(win):
    """Where the caret is, for "Pick up where you left off" next time."""
    ed = win.engine.ed
    path = win.engine.path
    if ed is None or not path or ed.story() != "body":
        return
    node = ed.caret_pos()[0]
    blocks = ed.body_blocks()
    i = next((k for k, b in enumerate(blocks) if b[1] == node), None)
    store = win.app.settings.setdefault("resume", {})
    if i is None or i < 3:
        store.pop(path, None)
    else:
        snippet = (ed.para_text_of(node) or "").replace("\ufffc", "").strip()
        store[path] = {"para": i, "snippet": snippet[:60], "time": time.time()}
        if len(store) > 50:
            for k in sorted(store, key=lambda k: store[k].get("time", 0))[:len(store) - 50]:
                store.pop(k, None)
    win.app.save_settings()


def _ago(t):
    d = time.time() - t
    if d < 120:
        return "a moment ago"
    if d < 3600:
        return "%d minutes ago" % (d // 60)
    if d < 86400 * 2:
        h = d // 3600
        return "%d hour%s ago" % (h, "" if h == 1 else "s")
    days = d // 86400
    return "%d days ago" % days


def offer_resume(win):
    path = win.engine.path
    if not path:
        return
    rec = win.app.settings.get("resume", {}).get(path)
    if not rec:
        return
    b = Gtk.Button()
    b.get_style_context().add_class("folio-resume")
    v = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
    t = Gtk.Label(xalign=0)
    t.set_markup("<b>Welcome back!</b>")
    v.pack_start(t, False, False, 0)
    v.pack_start(Gtk.Label(label="Pick up where you left off:", xalign=0), False, False, 0)
    s = Gtk.Label(label=(rec.get("snippet") or "")[:40] or "Paragraph %d" % rec["para"],
                  xalign=0)
    s.get_style_context().add_class("dim-label")
    v.pack_start(s, False, False, 0)
    w = Gtk.Label(label=_ago(rec.get("time", time.time())), xalign=0)
    w.get_style_context().add_class("dim-label")
    v.pack_start(w, False, False, 0)
    b.add(v)
    b.set_halign(Gtk.Align.END)
    b.set_valign(Gtk.Align.START)
    b.set_margin_end(24)
    b.set_margin_top(12)

    def go(*_):
        ed = win.engine.ed
        blocks = ed.body_blocks()
        if rec["para"] < len(blocks) and ed.goto_node(blocks[rec["para"]][1]):
            win.engine.view.after_move()
        close()
        win.focus_document()

    def close(*_):
        if b.get_parent() is not None:
            b.get_parent().remove(b)
        return False
    b.connect("clicked", go)
    win.canvas_overlay.add_overlay(b)
    b.show_all()
    GLib.timeout_add_seconds(20, close)
    win.canvas.get_vadjustment().connect(
        "value-changed", lambda a: close() if a.get_value() > 400 else None)
