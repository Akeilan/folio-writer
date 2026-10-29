"""Shape Format > Text: Text Direction, Align Text and Create Link /
Break Link, which makes text that overflows one text box carry on in
another, as in the original."""
from gi.repository import Gdk, GLib


DIRECTIONS = [("Horizontal", 0), ("Rotate all text 90°", 2), ("Rotate all text 270°", 5)]
ALIGN = [("Top", "TOP"), ("Middle", "CENTER"), ("Bottom", "BOTTOM")]


class Linker:
    """Create Link: the next click on an empty text box links to it."""

    def __init__(self, win):
        self.win = win
        self.src = None

    @property
    def pending(self):
        return self.src is not None

    def _native(self):
        return getattr(self.win.engine, "native", False)

    def create(self):
        ed = self.win.engine.ed
        o = ed.selected_object()
        if o is None or o["kind"] != "textbox":
            self.win.dialogs.message("Select a text box first.")
            return
        if ed.textbox_link_state() == "break":
            self.win.dialogs.message("This text box is already linked. Break the link first.")
            return
        self.src = ed.selected_objects()[0][0]
        self._cursor(True)
        self.win.status.flash("Click an empty text box to link to. Press Esc to cancel.")
        return

    def cancel(self):
        if self.src is not None:
            self.src = None
            self._cursor(False)
            self.win.status.flash("")

    def _cursor(self, on):
        gw = self.win.engine.view.get_window()
        if gw is None:
            return
        cur = Gdk.Cursor.new_from_name(gw.get_display(), "copy") if on else None
        gw.set_cursor(cur)

    def press(self, event):
        """A click while linking: let the click select, then link."""
        if self.src is None:
            return False
        if event.button != 1:
            self.cancel()
            return False
        src = self.src
        self.src = None
        self._cursor(False)
        GLib.timeout_add(250, lambda: (self._finish(src), False)[1])
        return False

    def _finish(self, src_name):
        ed = self.win.engine.ed
        o = ed.selected_object()
        if o is None or o["kind"] != "textbox":
            if ed.story() == "textbox":
                ed.leave_textbox()
                o = ed.selected_object()
        if o is None or o["kind"] != "textbox":
            self.win.status.flash("")
            return
        msg = ed.link_textboxes(src_name)
        self.win.engine.view.after_edit()
        if msg:
            self.win.dialogs.message(msg)
        else:
            self.win.status.flash("Text boxes linked.")
        self.win.update_object_tabs()
        return

    def break_link(self):
        ed = self.win.engine.ed
        if ed.unlink_textbox():
            self.win.engine.view.after_edit()
            self.win.status.flash("Link broken.")
            self.win.update_object_tabs()
        return

    def state(self):
        """'link' / 'break' / None for the ribbon button."""
        ed = self.win.engine.ed
        return (ed.textbox_link_state() or None) if ed is not None else None
