"""Arrange tools: the Selection Pane, aligning and distributing several
objects, and helpers for multi-object selections."""
from gi.repository import Gdk, GLib, Gtk, Pango

from . import bridge, docapi, icons
from .panes import Pane

MATH_CLSID = "078B7ABA-54FC-457F-8551-6147E776A997"


def all_objects(m):
    """Every floating or in-line object (shapes, pictures, text boxes, charts),
    front-most first, as (object, display name, kind)."""
    seen, out = set(), []
    for coll in (m.getDrawPage(),):
        for i in range(coll.getCount()):
            o = coll.getByIndex(i)
            try:
                name = o.Name or ""
            except Exception:
                name = ""
            try:
                if o.supportsService("com.sun.star.text.TextEmbeddedObject") and \
                        o.CLSID.upper() == MATH_CLSID:
                    continue
            except Exception:
                pass
            if name in seen and name:
                continue
            seen.add(name)
            out.append(o)
    try:
        out.sort(key=lambda o: -(o.ZOrder or 0))
    except Exception:
        pass
    return out


def display_name(o, i=0):
    try:
        n = o.Name
    except Exception:
        n = ""
    if n:
        return n
    try:
        t = o.getShapeType().split(".")[-1].replace("Shape", "")
    except Exception:
        t = "Object"
    return "%s %d" % (t or "Object", i + 1)



def select(m, objs):
    ctl = docapi.controller(m)
    if not objs:
        return
    if len(objs) == 1:
        ctl.select(objs[0])
        return
    coll = bridge.create("com.sun.star.drawing.ShapeCollection")
    for o in objs:
        coll.add(o)
    ctl.select(coll)


# ------------------------------------------------------------ align / distribute
def _box(o):
    """(x, y, w, h) of a floating object, mm100 in its anchor's coordinates."""
    s = o.Size
    return o.HoriOrientPosition, o.VertOrientPosition, s.Width, s.Height





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

    def refresh(self):
        m = self.model
        if m is None:
            return
        self._muted = True
        self.store.clear()
        for i, o in enumerate(all_objects(m)):
            try:
                vis = bool(o.Visible)
            except Exception:
                vis = True
            self.store.append([display_name(o, i), vis, o])
        self._muted = False

    def _click(self, tv, ev):
        res = tv.get_path_at_pos(int(ev.x), int(ev.y))
        if not res:
            return False
        path, col = res[0], res[1]
        if col is tv.get_column(1) and ev.button == 1:
            row = self.store[path]
            row[1] = not row[1]
            try:
                row[2].Visible = row[1]
            except Exception as e:
                print("visible:", e)
            return True
        return False

    def _selected(self, sel):
        if self._muted:
            return
        model, paths = sel.get_selected_rows()
        objs = [model[p][2] for p in paths if model[p][1]]
        if objs:
            try:
                select(self.model, objs)
            except Exception as e:
                print("select objects:", e)
            GLib.timeout_add(120, lambda: (self.win.update_object_tabs(), False)[1])

    def _renamed(self, cell, path, text):
        text = text.strip()
        if not text:
            return
        try:
            self.store[path][2].Name = text
            self.store[path][0] = text
        except Exception as e:
            self.win.dialogs.message("The name couldn't be changed: %s" % e)

    def show_all_objects(self, on):
        for row in self.store:
            try:
                row[2].Visible = on
                row[1] = on
            except Exception:
                pass

    def reorder(self, delta):
        model, paths = self.tv.get_selection().get_selected_rows()
        for p in paths:
            o = model[p][2]
            try:
                o.ZOrder = max(0, o.ZOrder + delta)
            except Exception:
                pass
        self.refresh()
