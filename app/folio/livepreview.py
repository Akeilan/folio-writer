"""Live Preview, as in the original: resting the pointer on a style, font,
size, colour, table style or picture style shows it in the document; moving
away puts things back. Nothing is changed until you click.

A preview is applied as one undo step and taken back with undo, so it never
reaches the undo list, and the document's "changed" flag is restored."""
from gi.repository import GLib

from . import docapi

TITLE = "Live Preview"
DELAY = 280          # ms of hovering before the preview shows (as the original)


class LivePreview:
    def __init__(self, win):
        self.win = win
        self.key = None
        self.active = False
        self._was_modified = False
        self._timer = 0
        self._end_timer = 0

    def enabled(self):
        return self.win.app.settings.get("live_preview", True)

    # ------------------------------------------------------------ hover API
    def hover(self, key, apply_fn):
        """The pointer rests on something previewable."""
        if not self.enabled():
            return
        if self._end_timer:
            GLib.source_remove(self._end_timer)
            self._end_timer = 0
        if key == self.key and self.active:
            return
        if self._timer:
            GLib.source_remove(self._timer)
        self._timer = GLib.timeout_add(DELAY, self._start, key, apply_fn)

    def unhover(self):
        """The pointer left: put the document back (a moment later, so moving
        from one item to the next doesn't flicker)."""
        if self._timer:
            GLib.source_remove(self._timer)
            self._timer = 0
        if self.active and not self._end_timer:
            self._end_timer = GLib.timeout_add(120, self._end_later)

    def commit(self):
        """A click: take the preview back first; the real command follows."""
        if self._timer:
            GLib.source_remove(self._timer)
            self._timer = 0
        self.end()

    # ------------------------------------------------------------ internals
    def _end_later(self):
        self._end_timer = 0
        self.end()
        return False

    def _start(self, key, apply_fn):
        self._timer = 0
        self.end()
        m = self.win.engine.model
        if m is None or self.win.read_only:
            return False
        try:
            self._was_modified = m.isModified()
            um = m.getUndoManager()
            um.enterUndoContext(TITLE)
            try:
                apply_fn(m)
            finally:
                um.leaveUndoContext()
            self.active = True
            self.key = key
        except Exception as e:
            print("live preview:", e)
            self._take_back(m)
        return False

    def _take_back(self, m):
        try:
            um = m.getUndoManager()
            titles = um.getAllUndoActionTitles()
            if titles and titles[0] == TITLE:
                um.undo()
                try:
                    um.clearRedo()
                except Exception:
                    pass
            if not self._was_modified and m.isModified():
                m.setModified(False)
        except Exception as e:
            print("live preview undo:", e)

    def end(self):
        if not self.active:
            return
        self.active = False
        self.key = None
        m = self.win.engine.model
        if m is not None:
            self._take_back(m)


# ---------------------------------------------------------------- helpers
def attach(win, widget, key, apply_fn):
    """Preview apply_fn(model) while the pointer rests on widget."""
    lp = win.live_preview
    widget.connect("enter-notify-event", lambda *_: (lp.hover(key, apply_fn), False)[1])
    widget.connect("leave-notify-event", lambda *_: (lp.unhover(), False)[1])
    # clicking: drop the preview before the real command runs
    widget.connect("button-press-event", lambda *_: (lp.commit(), False)[1])


def _targets(m):
    """Text ranges the preview applies to: the selection, or the word at the
    cursor for character formatting."""
    vc = docapi.view_cursor(m)
    return vc


def para_style(name):
    from .actions import engine_style, CHAR_STYLES

    def apply(m):
        vc = docapi.view_cursor(m)
        if name in CHAR_STYLES:
            rng = _word_or_selection(vc)
            rng.CharStyleName = engine_style(name)
        else:
            vc.ParaStyleName = engine_style(name)
    return apply


def _word_or_selection(vc):
    if not vc.isCollapsed():
        return vc
    c = vc.getText().createTextCursorByRange(vc.getStart())
    c.gotoStartOfWord(False)
    c.gotoEndOfWord(True)
    return c


def char_prop(**props):
    def apply(m):
        rng = _word_or_selection(docapi.view_cursor(m))
        for k, v in props.items():
            rng.setPropertyValue(k, v)
    return apply
