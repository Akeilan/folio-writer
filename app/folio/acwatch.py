"""The AutoCorrect Options button, as in the original: after AutoCorrect
changes what you typed, a small button appears under the change; its menu
changes it back, stops that correction from happening again, or opens the
AutoCorrect options.

Also the AutoCorrect features the engine lacks: capitalizing the names of
days, and leaving the first letter of table cells alone when that option is
off."""
import time

from gi.repository import GLib, Gtk, Pango, PangoCairo

from . import icons

TRIGGERS = {"space", "return", "kp_enter", "tab", "period", "comma", "semicolon", "colon",
            "exclam", "question", "parenright", "quotedbl", "apostrophe"}
DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


class ACWatch:
    def __init__(self, win, overlay):
        self.win = win
        self.overlay = overlay
        self.last = None
        self.pending = None
        btn = Gtk.Button()
        btn.get_style_context().add_class("folio-acbutton")
        btn.add(icons.image("cmd/sc_autocorrectdlg" if icons.exists("cmd/sc_autocorrectdlg")
                            else "cmd/sc_spellingandgrammardialog", 16))
        btn.set_tooltip_text("AutoCorrect Options")
        btn.set_halign(Gtk.Align.START)
        btn.set_valign(Gtk.Align.START)
        btn.set_no_show_all(True)
        btn.set_focus_on_click(False)
        btn.connect("clicked", lambda *_: self.menu())
        overlay.add_overlay(btn)
        self.btn = btn
        self.keys_since = 0
        win.engine.view.connect("button-press-event",
                                lambda *_: (self.hide(), setattr(self, "typed", ""), False)[2])
        win.canvas.get_vadjustment().connect("value-changed", lambda *_: self.hide())

    def settings(self):
        return self.win.app.settings

    def tab_indent(self, keyname, mods):
        """Tab at the start of a paragraph sets its first-line indent;
        Backspace there takes it away (AutoFormat As You Type)."""
        if mods or keyname not in ("tab", "backspace") or \
                not self.settings().get("ac_tab_indent", True):
            return False
        return self._tab_indent_native(keyname)

    def _tab_indent_native(self, keyname):
        eng = self.win.engine
        ed = eng.ed
        if ed is None or ed.has_selection() or ed.cell_name() or ed.list_info() is not None:
            return False
        p, off = ed.caret_pos()
        if off != 0:
            return False
        d = ed.state() or {}
        first = d.get("ind_first", 0) or 0
        left = d.get("ind_left", 0) or 0
        if keyname == "tab":
            if not ed.para_text_of(p).strip():
                return False
            if first < 720:
                ed.set_indent(None, None, 720)
            else:
                ed.set_indent(left + 720, None, None)
            eng.view.after_edit()
            return True
        if first > 0:
            ed.set_indent(None, None, 0)
        elif left > 0:
            ed.set_indent(max(0, left - 720), None, None)
        else:
            return False
        eng.view.after_edit()
        return True

    def note(self, old, new, kind):
        """The new engine's AutoCorrect made a change: the button goes under it."""
        self.last = {"native": True, "old": old, "new": new, "kind": kind}
        if not self.settings().get("ac_buttons", True):
            return
        self.keys_since = 0
        GLib.timeout_add(60, self._place_native, new)

    def _place_native(self, new):
        eng = self.win.engine
        ed = eng.ed
        if ed is None or self.last is None:
            return False
        r = ed.caret_rect()
        if not r:
            return False
        v = eng.view
        x, y = v.to_widget(r[0], r[1], r[2])
        h = r[3] * v.ppp
        try:
            back = self._text_px(new + " ")
        except Exception:
            back = len(new) * 7
        res = v.translate_coordinates(self.overlay, int(x - back), int(y + h) + 1)
        if not res:
            return False
        ox, oy = res
        self.btn.set_margin_start(max(0, ox))
        self.btn.set_margin_top(max(0, oy))
        self.btn.get_child().show_all()
        self.btn.show()
        return False

    # ------------------------------------------------------------ keys
    typed = ""
    enters = 0

    def before_key(self, keyname, mods, event=None):
        """Called for every key the document gets. What was typed is
        followed here (the engine may still be catching up)."""
        if self.btn.get_visible():
            self.keys_since += 1
            if self.keys_since > 12:
                self.hide()
        return False



    # ------------------------------------------------------------ button
    def _text_px(self, text):
        import cairo
        eng = self.win.engine
        try:
            size = float(eng.get(".uno:FontHeight") or 11)
        except ValueError:
            size = 11.0
        font = eng.get(".uno:CharFontName") or "Carlito"
        layout = PangoCairo.create_layout(cairo.Context(
            cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1)))
        layout.set_font_description(Pango.FontDescription("%s %spx" % (font, size * 96 / 72.0)))
        layout.set_text(text, -1)
        w, _h = layout.get_pixel_size()
        return w * (eng.view.get_zoom() or 1.0)

    def hide(self):
        self.btn.hide()

    def menu(self):
        last = self.last
        if last is None:
            return
        from .ribbon import menu_popover
        old, new, kind = last["old"], last["new"], last["kind"]
        if kind == "caps":
            items = [("Undo Automatic Capitalization", lambda: self.change_back()),
                     ("Stop Auto-capitalizing First Letter of Sentences",
                      lambda: self.stop("ac_caps_first"))]
        elif kind == "days":
            items = [("Undo Automatic Capitalization", lambda: self.change_back()),
                     ("Stop Capitalizing Names of Days", lambda: self.stop("ac_days"))]
        else:
            items = [("Change back to “%s”" % old, lambda: self.change_back()),
                     ("Stop Automatically Correcting “%s”" % old, lambda: self.stop_word())]
        items += [None, ("Control AutoCorrect Options...",
                         lambda: GLib.idle_add(lambda: (self.win.dialogs.autocorrect_options(),
                                                        False)[1]))]
        pop = menu_popover(self.btn, items)
        pop.popup()

    def change_back(self):
        last, self.last = self.last, None
        self.hide()
        if last is None:
            return
        ac = getattr(self.win.engine.view, "autocorrect", None)
        if ac is not None and ac.undo_last():
            self.win.engine.view.after_edit()
        self.win.focus_document()

    def stop(self, key):
        self.change_back()
        self.settings()[key] = False
        self.win.app.save_settings()

    def stop_word(self):
        last = self.last
        self.change_back()
        if last is None:
            return
        try:
            from . import options
            options.remove_autocorrect_entry(self.win, last["old"])
        except Exception as e:
            print("autocorrect stop:", e)
