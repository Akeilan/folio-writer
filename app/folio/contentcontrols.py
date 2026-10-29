"""Developer > Controls: content controls (rich text, plain text, picture,
check box, combo box, drop-down list, date picker), their Properties, and
the pickers that open when you click a drop-down or date control."""
import datetime

from gi.repository import Gdk, GLib, Gtk

from .widgets import FDialog, grid


def _native(win):
    from .native import controls
    return controls


def insert(win, kind):
    return _native(win).insert(win, kind)


def properties(win):
    return _native(win).properties(win)
