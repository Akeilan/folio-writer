# An "other application": owns the clipboard and offers text to drag.
import sys
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib
mode = sys.argv[1] if len(sys.argv) > 1 else "both"
win = Gtk.Window(title="ExternalApp")
win.move(1320, 120)
win.set_default_size(240, 120)
ev = Gtk.EventBox()
lab = Gtk.Label(label="DRAG ME")
ev.add(lab)
win.add(ev)
TEXT = "Dragged from outside"
HTML = "<b>Dragged</b> from outside"
targets = [Gtk.TargetEntry.new("text/html", 0, 0), Gtk.TargetEntry.new("UTF8_STRING", 0, 1),
           Gtk.TargetEntry.new("text/plain;charset=utf-8", 0, 1), Gtk.TargetEntry.new("text/plain", 0, 1),
           Gtk.TargetEntry.new("STRING", 0, 1)]
ev.drag_source_set(Gdk.ModifierType.BUTTON1_MASK, targets, Gdk.DragAction.COPY | Gdk.DragAction.MOVE)
def get(w, ctx, data, info, t):
    if info == 0:
        data.set(Gdk.Atom.intern("text/html", False), 8, HTML.encode())
    else:
        data.set_text(TEXT, -1)
ev.connect("drag-data-get", get)
def own():
    cb = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
    if mode == "html":
        def cget(c, sel, info, d):
            if info == 0:
                sel.set(Gdk.Atom.intern("text/html", False), 8, b"<i>External</i> rich clipboard")
            else:
                sel.set_text("External rich clipboard", -1)
        cb.set_with_data(targets, cget, lambda *a: None, None)
    else:
        cb.set_text("External clipboard text", -1)
    print("owned", flush=True)
    return False
GLib.timeout_add(500, own)
win.show_all()
Gtk.main()
