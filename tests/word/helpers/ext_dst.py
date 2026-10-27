import sys, gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk
out = sys.argv[1]
win = Gtk.Window(title="ExternalDrop")
win.move(1320, 400); win.set_default_size(260, 200)
lab = Gtk.Label(label="DROP HERE")
ev = Gtk.EventBox(); ev.add(lab); win.add(ev)
ev.drag_dest_set(Gtk.DestDefaults.ALL, [Gtk.TargetEntry.new("UTF8_STRING", 0, 1), Gtk.TargetEntry.new("text/plain", 0, 1)], Gdk.DragAction.COPY)
def rec(w, ctx, x, y, data, info, t):
    open(out, "w").write(data.get_text() or "")
ev.connect("drag-data-received", rec)
win.show_all(); Gtk.main()
