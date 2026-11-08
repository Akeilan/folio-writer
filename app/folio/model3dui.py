"""Insert > 3D Models (W4-01): bring a glTF model into the document, turn it with the mouse or
from the 3D Model Views gallery, and reset it. The model travels in the .docx as Word keeps it —
a .glb part with a picture of the view it is turned to — so Word opens it as a model that can be
turned again, and every other reader sees the picture.

The engine writes the parts and the drawing (insert_model3d / selected_model3d / set_model3d);
the reading and the drawing of the model itself is model3d.py, shared with Folio Show.
"""
import os

from gi.repository import Gtk

# the named views Word offers, as (rx, ry, rz) degrees
VIEWS = [("Front", (0, 0, 0)), ("Back", (0, 180, 0)), ("Left", (0, 90, 0)), ("Right", (0, -90, 0)),
         ("Top", (90, 0, 0)), ("Bottom", (-90, 0, 0)),
         ("Above Front Left", (25, 35, 0)), ("Above Front Right", (25, -35, 0)),
         ("Below Front Left", (-25, 35, 0)), ("Below Front Right", (-25, -35, 0))]
DEFAULT_ROT = (15.0, -30.0, 0.0)
PATTERNS = ["*.glb", "*.gltf"]


def _ed(win):
    return win.engine.ed


def _mesh(win, glb):
    from . import model3d
    return model3d.Mesh(glb)


def insert(win, path=None):
    """Insert > 3D Models > This Device. Returns the model's part, or None."""
    from . import model3d
    if path is None:
        path = win.dialogs.pick_file("Insert 3D Model", PATTERNS, "3D Models")
        if not path:
            return None
    try:
        _data, glb = model3d.load_file(path)
        mesh = model3d.Mesh(glb)
    except Exception as e:                      # noqa: BLE001  any unreadable model lands here
        win.dialogs.message("Folio Page can't read this 3D model.\n\n%s" % e)
        return None
    ed = _ed(win)
    pg = ed.caret_page()
    top, right, _b, left = ed.page_margins(pg)
    col = max(72.0, ed.page_size(pg)[0] - left - right) if hasattr(ed, "page_size") else 468.0
    w = h = min(288.0, col)
    png = mesh.png(int(w * 2), int(h * 2), DEFAULT_ROT)
    name = os.path.splitext(os.path.basename(path))[0]
    part = ed.insert_model3d(glb, png, w, h, *DEFAULT_ROT, name)
    if not part:
        win.dialogs.message("That 3D model couldn't be put in the document.")
        return None
    win.engine.view.after_edit()
    try:
        win.update_object_tabs()
    except Exception as e:                      # noqa: BLE001
        print("3d model:", e)
    return part


def selected(win):
    """(model part, (rx, ry, rz)) when a 3-D model is selected, else None."""
    ed = _ed(win)
    try:
        return ed.selected_model3d()
    except Exception as e:                      # noqa: BLE001
        print("3d model:", e)
        return None


def turn(win, rot, absolute=False):
    """Turn the selected model. `rot` is degrees; absolute=False adds to where it is."""
    from . import model3d
    got = selected(win)
    if got is None:
        win.status.flash("Select a 3D model first.")
        return None
    _part, cur = got
    new = tuple(float(v) for v in rot) if absolute else tuple((a + b) % 360.0 for a, b in zip(cur, rot))
    new = tuple((v + 180.0) % 360.0 - 180.0 for v in new)
    ed = _ed(win)
    glb = bytes(ed.model3d_glb() or b"")
    try:
        mesh = model3d.Mesh(glb)
    except Exception as e:                      # noqa: BLE001
        win.dialogs.message("The model in this document can't be read again.\n\n%s" % e)
        return None
    o = ed.selected_object() or {}
    w = max(16.0, float(o.get("w") or 216.0))
    h = max(16.0, float(o.get("h") or 216.0))
    png = mesh.png(int(w * 2), int(h * 2), new)
    if not ed.set_model3d(png, *new):
        return None
    win.engine.view.after_edit()
    return new


def view(win, name):
    """3D Model > 3D Model Views: one of the named views."""
    key = (name or "").strip().lower().replace(" ", "-")
    for label, rot in VIEWS:
        if label.lower().replace(" ", "-") == key:
            return turn(win, rot, absolute=True)
    win.status.flash("There is no 3D view called “%s”." % name)
    return None


def reset(win):
    return turn(win, DEFAULT_ROT, absolute=True)


NUDGE = {"left": (0, -15, 0), "right": (0, 15, 0), "up": (-15, 0, 0), "down": (15, 0, 0),
         "clockwise": (0, 0, 15), "anticlockwise": (0, 0, -15)}


def nudge(win, way):
    """Turn the model a step: left, right, up, down, clockwise, anticlockwise."""
    step = NUDGE.get((way or "").strip().lower())
    if step is None:
        win.status.flash("Turn a 3D model left, right, up, down, clockwise or anticlockwise.")
        return None
    return turn(win, step)


def turn_dialog(win):
    """3D Model > Turn: the exact angles, for a view the gallery doesn't offer."""
    from .widgets import FDialog, grid, heading
    got = selected(win)
    if got is None:
        win.status.flash("Select a 3D model first.")
        return None
    cur = got[1]
    d = FDialog(win, "Turn 3D Model")
    spins = {}
    rows = []
    for key, label, i in (("x", "_X (tip forwards):", 0), ("y", "_Y (swing round):", 1), ("z", "_Z (spin):", 2)):
        sp = Gtk.SpinButton.new_with_range(-180, 180, 5)
        sp.set_value(round(cur[i]))
        spins[key] = sp
        rows.append([label, sp])
    d.add(heading("Degrees"))
    d.add(grid(rows))
    d.spins = spins                     # the tests set the angles by name, not by position
    d.show_all()
    out = None
    if d.run() == Gtk.ResponseType.OK:
        out = turn(win, tuple(spins[k].get_value() for k in ("x", "y", "z")), absolute=True)
    d.destroy()
    return out
