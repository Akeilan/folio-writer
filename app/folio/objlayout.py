"""Pictures and shapes, the rest of the original's layout features: the
Layout dialog (Position, Text Wrapping, Size), Edit Wrap Points, Move with
Text / Fix Position on Page, Crop to Shape, Crop Fill / Fit, and the Glow
and Soft Edges effects."""
import math
import os
import tempfile

from gi.repository import Gdk, GdkPixbuf, Gtk

from .widgets import FDialog, LengthSpin, combo, grid, heading

# RelOrientation
FRAME, PRINT_AREA, CHAR, PAGE_LEFT, PAGE_RIGHT, PAGE_FRAME, PAGE_PRINT_AREA, TEXT_LINE = \
    0, 1, 2, 3, 4, 7, 8, 9


def layout_dialog(win, tab=0):
    from .native import arrange
    return arrange.layout_dialog(win, tab)


def edit_wrap_points(win):
    """Wrap points around the picture: drag a point to change where text
    wraps; text wraps tightly along them."""
    from .native import arrange
    return arrange.edit_wrap_points(win)


CROP_SHAPES = [("Rectangle", "rectangle"), ("Rounded Rectangle", "round-rectangle"),
               ("Oval", "ellipse"), ("Triangle", "isosceles-triangle"),
               ("Right Triangle", "right-triangle"), ("Diamond", "diamond"),
               ("Pentagon", "pentagon"), ("Hexagon", "hexagon"), ("Octagon", "octagon"),
               ("Parallelogram", "parallelogram"), ("Trapezoid", "trapezoid"),
               ("Star: 5 Points", "star5"), ("Heart", "heart"), ("Cloud", "cloud"),
               ("Arrow: Right", "right-arrow"), ("Chevron", "chevron")]


def crop_to_shape(win, kind):
    """Replace the picture by a shape of that kind filled with the picture
    (the same size and place)."""
    from .native import arrange
    return arrange.crop_to_shape(win, kind)


# ================================================================ effects
GLOWS = [("No Glow", 0, None)] + [
    ("Glow: %g pt; %s" % (pt, name), pt, col) for pt in (5, 8, 11, 18)
    for name, col in (("Blue, Accent color 1", 0x4472C4), ("Orange, Accent color 2", 0xED7D31),
                      ("Gold, Accent color 4", 0xFFC000), ("Green, Accent color 6", 0x70AD47))]
SOFT = [("No Soft Edges", 0)] + [("%g Point" % p, p) for p in (1, 2.5, 5, 10, 25, 50)]


