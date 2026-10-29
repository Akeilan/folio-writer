"""Outline view: the document as an outline — headings with expand/collapse
symbols, body text under them, indented by level. Edit text in place,
promote/demote, move sections up and down, drag to reorder, show levels."""
import html

from gi.repository import Gdk, GLib, Gtk, Pango

from .actions import engine_style, word_style
from . import modelapi

BODY = 10     # level used for body text


class OutlineView(Gtk.Box):
    def __init__(self, win):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)
        self.win = win
        self.show_formatting = True
        self.first_line_only = False
        self.max_level = 9
        self.store = Gtk.TreeStore(str, str, int, object)   # markup, symbol, level, para
        self.tv = Gtk.TreeView(model=self.store)
        self.tv.set_headers_visible(False)
        self.tv.set_enable_tree_lines(False)
        self.tv.set_show_expanders(False)
        self.tv.set_level_indentation(28)
        self.tv.get_style_context().add_class("folio-outline")
        sym = Gtk.CellRendererText()
        sym.set_property("xpad", 6)
        col0 = Gtk.TreeViewColumn("", sym, text=1)
        self.tv.append_column(col0)
        self.cell = Gtk.CellRendererText()
        self.cell.set_property("editable", True)
        self.cell.set_property("wrap-mode", Pango.WrapMode.WORD)
        self.cell.connect("edited", self._edited)
        self.cell.connect("editing-started", self._editing_started)
        col = Gtk.TreeViewColumn("", self.cell, markup=0)
        col.set_expand(True)
        self.tv.append_column(col)
        self.tv.connect("size-allocate", self._wrap_width)
        self.tv.connect("row-activated", self._toggle_row)
        self.tv.connect("key-press-event", self._key)
        self.tv.connect("button-press-event", self._click)
        # drag a heading (with its content) to a new place
        self.tv.enable_model_drag_source(Gdk.ModifierType.BUTTON1_MASK,
                                         [Gtk.TargetEntry.new("folio-outline",
                                                              Gtk.TargetFlags.SAME_WIDGET, 0)],
                                         Gdk.DragAction.MOVE)
        self.tv.enable_model_drag_dest([Gtk.TargetEntry.new(
            "folio-outline", Gtk.TargetFlags.SAME_WIDGET, 0)], Gdk.DragAction.MOVE)
        self.tv.connect("drag-data-get", lambda *a: None)
        self.tv.connect("drag-data-received", self._dropped)
        sw = Gtk.ScrolledWindow()
        sw.add(self.tv)
        self.pack_start(sw, True, True, 0)
        self.collapsed = set()

    # ------------------------------------------------------------ build
    def load(self, keep_selection=True):
        """Fill the outline from the document (native/views.py)."""
        raise NotImplementedError

    def _symbols(self, parent):
        """Word's outline symbols: ⊕ heading with content under it, ⊖ heading
        without, ○ body text."""
        it = self.store.iter_children(parent)
        while it is not None:
            level = self.store[it][2]
            if level == BODY:
                sym = "○"
            else:
                sym = "⊕" if self.store.iter_has_child(it) else "⊖"
            self.store[it][1] = sym
            self._symbols(it)
            it = self.store.iter_next(it)

    def _markup(self, p, level):
        text = p.getString()
        if self.first_line_only and level == BODY and len(text) > 90:
            text = text[:90].rstrip() + "…"
        esc = html.escape(text) or "<i> </i>"
        if not self.show_formatting:
            return esc
        try:
            size = min(20, max(9, float(p.CharHeight)))
            attrs = ["size='%gpt'" % size]
            if p.CharWeight >= 150:
                attrs.append("weight='bold'")
            if getattr(p.CharPosture, "value", "NONE") != "NONE":
                attrs.append("style='italic'")
            if p.CharColor not in (-1, None) and p.CharColor >= 0:
                attrs.append("foreground='#%06x'" % (p.CharColor & 0xFFFFFF))
            fam = p.CharFontName
            if fam:
                attrs.append("font_family='%s'" % html.escape(fam))
            return "<span %s>%s</span>" % (" ".join(attrs), esc)
        except Exception:
            return esc

    def _wrap_width(self, tv, alloc):
        self.cell.set_property("wrap-width", max(200, alloc.width - 80))

    # ------------------------------------------------------------ helpers
    def _selected(self):
        model, it = self.tv.get_selection().get_selected()
        return it

    def _selected_para(self):
        it = self._selected()
        return self.store[it][3] if it is not None else None

    def _toggle_row(self, tv, path, col):
        if tv.row_expanded(path):
            tv.collapse_row(path)
            self.collapsed.add(path.to_string())
        else:
            tv.expand_row(path, False)
            self.collapsed.discard(path.to_string())

    def _click(self, tv, ev):
        res = tv.get_path_at_pos(int(ev.x), int(ev.y))
        if not res:
            return False
        path, col = res[0], res[1]
        if col is tv.get_column(0) and ev.button == 1 and \
                self.store.iter_has_child(self.store.get_iter(path)):
            self._toggle_row(tv, path, col)
            tv.get_selection().select_path(path)
            return True
        if ev.button == 1:
            self._goto(self.store[path][3])
        return False

    def _key(self, tv, ev):
        st = ev.state & (Gdk.ModifierType.SHIFT_MASK | Gdk.ModifierType.MOD1_MASK |
                         Gdk.ModifierType.CONTROL_MASK)
        alt_shift = Gdk.ModifierType.SHIFT_MASK | Gdk.ModifierType.MOD1_MASK
        k = ev.keyval
        if st == alt_shift and k in (Gdk.KEY_Left, Gdk.KEY_Right):
            self.change_level(-1 if k == Gdk.KEY_Left else 1)
            return True
        if st == alt_shift and k in (Gdk.KEY_Up, Gdk.KEY_Down):
            self.move(-1 if k == Gdk.KEY_Up else 1)
            return True
        if st == alt_shift and k in (Gdk.KEY_plus, Gdk.KEY_equal, Gdk.KEY_KP_Add):
            self.expand(True)
            return True
        if st == alt_shift and k in (Gdk.KEY_minus, Gdk.KEY_underscore, Gdk.KEY_KP_Subtract):
            self.expand(False)
            return True
        if st == (Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK) and \
                k in (Gdk.KEY_N, Gdk.KEY_n):
            self.set_level(BODY)
            return True
        if st == alt_shift and Gdk.KEY_1 <= k <= Gdk.KEY_9:
            self.show_level(k - Gdk.KEY_0)
            return True
        if st == alt_shift and k in (Gdk.KEY_a, Gdk.KEY_A):
            self.show_level(9)
            return True
        if k == Gdk.KEY_Escape:
            return False
        if k in (Gdk.KEY_F2, Gdk.KEY_Return) and not st:
            it = self._selected()
            if it is not None:
                path = self.store.get_path(it)
                self.tv.set_cursor(path, self.tv.get_column(1), True)
                return True
        return False

    # ------------------------------------------------------------ commands
    def change_level(self, delta):
        it = self._selected()
        if it is None:
            return
        level = self.store[it][2]
        if level == BODY:
            new = 9 if delta < 0 else BODY
            if delta < 0:
                # body text promoted becomes a heading one deeper than its parent
                parent = self.store.iter_parent(it)
                new = min(9, (self.store[parent][2] + 1) if parent is not None else 1)
        else:
            new = level + delta
            if new < 1:
                return
            if new > 9:
                new = BODY
        self.set_level(new)

    def expand(self, on):
        it = self._selected()
        if it is None:
            return
        path = self.store.get_path(it)
        if on:
            self.tv.expand_row(path, False)
            self.collapsed.discard(path.to_string())
        else:
            self.tv.collapse_row(path)
            self.collapsed.add(path.to_string())

    def show_level(self, n):
        self.max_level = n
        self.collapsed.clear()
        self.load(keep_selection=False)

    def set_show_formatting(self, on):
        self.show_formatting = on
        self.load()

    def set_first_line_only(self, on):
        self.first_line_only = on
        self.load()
