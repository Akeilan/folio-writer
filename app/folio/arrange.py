"""Arrange tools: the Selection Pane, aligning and distributing several
objects, and helpers for multi-object selections."""
from gi.repository import Gdk, GLib, Gtk, Pango

from . import icons
from .panes import Pane


# ------------------------------------------------------------ selection pane
class SelectionPane(Pane):
    TITLE = "Selection"
    WIDTH = 260

    def __init__(self, win):
        Pane.__init__(self, win)
        bar = Gtk.Box(spacing=4)
        for label, cb in (("Show All", lambda: self.show_all_objects(True)),
                          ("Hide All", lambda: self.show_all_objects(False))):
            b = Gtk.Button(label=label)
            b.connect("clicked", lambda _b, cb=cb: cb())
            bar.pack_start(b, False, False, 0)
        for icon, tip, d in (("pan-up-symbolic", "Bring Forward", 1),
                             ("pan-down-symbolic", "Send Backward", -1)):
            b = Gtk.Button()
            b.add(Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.MENU))
            b.set_tooltip_text(tip)
            b.connect("clicked", lambda _b, d=d: self.reorder(d))
            bar.pack_end(b, False, False, 0)
        self.pack_start(bar, False, False, 0)
        self.store = Gtk.ListStore(str, bool, object)
        self.tv = Gtk.TreeView(model=self.store)
        self.tv.set_headers_visible(False)
        self.tv.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)
        name = Gtk.CellRendererText()
        name.set_property("editable", True)
        name.set_property("ellipsize", Pango.EllipsizeMode.END)
        name.connect("edited", self._renamed)
        col = Gtk.TreeViewColumn("", name, text=0)
        col.set_expand(True)
        self.tv.append_column(col)
        eye = Gtk.CellRendererPixbuf()
        eyecol = Gtk.TreeViewColumn("", eye)
        eyecol.set_cell_data_func(eye, self._eye)
        self.tv.append_column(eyecol)
        self.tv.connect("button-press-event", self._click)
        self._muted = False
        self.tv.get_selection().connect("changed", self._selected)
        sw = Gtk.ScrolledWindow()
        sw.add(self.tv)
        self.pack_start(sw, True, True, 0)

    def _eye(self, col, cell, model, it, data):
        cell.set_property("icon-name", "view-reveal-symbolic" if model[it][1] else
                          "view-conceal-symbolic")

    def on_shown(self):
        self.refresh()
