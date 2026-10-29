"""Shapes and text boxes: pick a shape, then drag on the page to draw it
(a plain click gives the default 1" size). Built through the document model
so the result is an ordinary shape or text box in the file."""
from gi.repository import Gdk, GLib



SHAPE_MENU = [
    ("#", "Lines"), ("Line", "line"), ("Arrow", "arrow-line"),
    ("Connector: Elbow", "elbow-connector"), ("Connector: Curved", "curved-connector"),
    ("Freeform: Scribble", "scribble"),
    ("#", "Rectangles"), ("Rectangle", "rectangle"), ("Rounded Rectangle", "round-rectangle"),
    ("#", "Basic Shapes"), ("Oval", "ellipse"), ("Triangle", "isosceles-triangle"),
    ("Right Triangle", "right-triangle"), ("Parallelogram", "parallelogram"),
    ("Trapezoid", "trapezoid"), ("Diamond", "diamond"), ("Pentagon", "pentagon"),
    ("Hexagon", "hexagon"), ("Octagon", "octagon"), ("Frame", "frame"), ("Donut", "ring"),
    ("Cube", "cube"), ("Can", "can"), ("Heart", "heart"), ("Lightning Bolt", "lightning"),
    ("Sun", "sun"), ("Moon", "moon"), ("Smiley Face", "smiley"), ("Cloud", "cloud"),
    ("#", "Block Arrows"), ("Right Arrow", "right-arrow"), ("Left Arrow", "left-arrow"),
    ("Up Arrow", "up-arrow"), ("Down Arrow", "down-arrow"),
    ("Left-Right Arrow", "left-right-arrow"), ("Up-Down Arrow", "up-down-arrow"),
    ("Notched Right Arrow", "notched-right-arrow"), ("Chevron", "chevron"),
    ("Circular Arrow", "circular-arrow"),
    ("#", "Equation Shapes"), ("Plus Sign", "math-plus"), ("Minus Sign", "math-minus"),
    ("Multiplication Sign", "math-multiply"), ("Division Sign", "math-divide"),
    ("Equal", "math-equal"), ("Not Equal", "math-not-equal"),
    ("#", "Flowchart"), ("Process", "flowchart-process"), ("Decision", "flowchart-decision"),
    ("Terminator", "flowchart-terminator"), ("Document", "flowchart-document"),
    ("Data", "flowchart-data"), ("Connector", "flowchart-connector"),
    ("#", "Stars and Banners"), ("Star: 4 Points", "star4"), ("Star: 5 Points", "star5"),
    ("Star: 6 Points", "star6"), ("Star: 8 Points", "star8"), ("Star: 24 Points", "star24"),
    ("Scroll: Horizontal", "horizontal-scroll"),
    ("#", "Callouts"), ("Speech Bubble: Rectangle", "rect-callout"),
    ("Speech Bubble: Rounded Rectangle", "callout"), ("Speech Bubble: Oval", "oval-callout"),
    ("Thought Bubble: Cloud", "cloud-callout"),
    None, ("Text Box", "textbox"), ("New Drawing Canvas", "canvas"),
]

# the menu's kinds as DrawingML presets (the new engine)
PRST = {
    "line": "line", "arrow-line": "straightConnector1", "elbow-connector": "bentConnector3",
    "curved-connector": "curvedConnector3", "rectangle": "rect", "round-rectangle": "roundRect",
    "ellipse": "ellipse", "isosceles-triangle": "triangle", "right-triangle": "rtTriangle",
    "parallelogram": "parallelogram", "trapezoid": "trapezoid", "diamond": "diamond",
    "pentagon": "pentagon", "hexagon": "hexagon", "octagon": "octagon", "frame": "frame",
    "math-plus": "mathPlus", "math-minus": "mathMinus", "math-multiply": "mathMultiply",
    "math-divide": "mathDivide", "math-equal": "mathEqual", "math-not-equal": "mathNotEqual",
    "ring": "donut", "cube": "cube", "can": "can", "heart": "heart", "lightning": "lightningBolt",
    "sun": "sun", "moon": "moon", "smiley": "smileyFace", "cloud": "cloud",
    "right-arrow": "rightArrow", "left-arrow": "leftArrow", "up-arrow": "upArrow",
    "down-arrow": "downArrow", "left-right-arrow": "leftRightArrow", "up-down-arrow": "upDownArrow",
    "notched-right-arrow": "notchedRightArrow", "chevron": "chevron", "circular-arrow": "circularArrow",
    "flowchart-process": "flowChartProcess", "flowchart-decision": "flowChartDecision",
    "flowchart-terminator": "flowChartTerminator", "flowchart-document": "flowChartDocument",
    "flowchart-data": "flowChartInputOutput", "flowchart-connector": "flowChartConnector",
    "star4": "star4", "star5": "star5", "star6": "star6", "star8": "star8", "star24": "star24",
    "horizontal-scroll": "horizontalScroll", "rect-callout": "wedgeRectCallout",
    "callout": "wedgeRoundRectCallout", "oval-callout": "wedgeEllipseCallout",
    "cloud-callout": "cloudCallout", "textbox": "textbox",
}


class DrawMode:
    def __init__(self, win):
        self.win = win
        self.kind = None
        self.start = None
        self.cur = None
        view = win.engine.view
        view.connect("button-press-event", self._press)
        view.connect("motion-notify-event", self._motion)
        view.connect("button-release-event", self._release)
        view.connect_after("draw", self._draw)
        view.add_events(Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.BUTTON_MOTION_MASK)

    def begin(self, kind):
        self.kind = kind
        self.start = self.cur = None
        w = self.win.engine.view.get_window()
        if w is not None:
            w.set_cursor(Gdk.Cursor.new_from_name(w.get_display(), "crosshair"))
        self.win.status.flash("Drag on the page to draw. Esc cancels.")

    def cancel(self):
        self.kind = None
        self.start = self.cur = None
        w = self.win.engine.view.get_window()
        if w is not None:
            w.set_cursor(None)
        self.win.engine.view.queue_draw()

    @property
    def active(self):
        return self.kind is not None

    # -------------------------------------------------------------- events
    def _press(self, view, ev):
        if not self.active or ev.button != 1:
            return False
        self.start = (ev.x, ev.y)
        self.cur = (ev.x, ev.y)
        return True

    def _motion(self, view, ev):
        if not self.active or self.start is None:
            return False
        self.cur = (ev.x, ev.y)
        view.queue_draw()
        return True

    def _release(self, view, ev):
        if not self.active or self.start is None or ev.button != 1:
            return False
        x0, y0 = self.start
        x1, y1 = ev.x, ev.y
        kind = self.kind
        self.cancel()
        GLib.idle_add(lambda: (self._create(kind, x0, y0, x1, y1), False)[1])
        return True

    def _draw(self, view, cr):
        if not self.active or self.start is None or self.cur is None:
            return False
        x0, y0 = self.start
        x1, y1 = self.cur
        cr.set_source_rgba(0.27, 0.45, 0.77, 0.25)
        cr.rectangle(min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0))
        cr.fill_preserve()
        cr.set_source_rgb(0.18, 0.32, 0.56)
        cr.set_line_width(1)
        cr.stroke()
        return False

    # -------------------------------------------------------------- create
    def _create_native(self, kind, x0, y0, x1, y1):
        view = self.win.engine.view
        ed = self.win.engine.ed
        a = view.page_at(x0, y0)
        b = view.page_at(x1, y1)
        if a is None:
            return
        pg, px0, py0 = a
        px1, py1 = (b[1], b[2]) if b is not None and b[0] == pg else (px0, py0)
        lines = kind in ("line", "arrow-line", "elbow-connector", "curved-connector")
        w, h = px1 - px0, py1 - py0
        if abs(w) < 4 and abs(h) < 4:      # a click: Word's default size
            w, h = 72.0, (0.0 if kind in ("line", "arrow-line") else 36.0 if kind == "textbox" or lines else 72.0)
        if not lines:
            px0, py0, w, h = min(px0, px0 + w), min(py0, py0 + h), abs(w), abs(h)
        label = next((it[0] for it in SHAPE_MENU if it and it[0] != "#" and it[1] == kind), "Shape")
        label = {"Arrow": "Straight Arrow Connector", "Line": "Straight Connector"}.get(label, label)
        ok = ed.insert_shape(PRST.get(kind, "rect"), pg, px0, py0, w, h, label, kind == "arrow-line")
        if ok:
            view.document_changed()
            view.objs.refresh()
            view.after_move()
            view.grab_focus()

    def _create(self, kind, x0, y0, x1, y1):
        return self._create_native(kind, x0, y0, x1, y1)


PICTURE_STYLES = [
    # (name, border pt, border colour, shadow)
    ("none", 0, 0, False),
    ("Simple Frame, White", 7, 0xFFFFFF, True),
    ("Simple Frame, Black", 7, 0x000000, False),
    ("Thick Matte, Black", 14, 0x000000, True),
    ("Drop Shadow Rectangle", 0, 0, True),
    ("Metal Frame", 6, 0x8C8C8C, True),
    ("Thin Frame, Gray", 1.5, 0x7F7F7F, False),
]


# ---------------------------------------------------------------- shape styles
ACCENTS = [0x000000, 0x4472C4, 0xED7D31, 0xA5A5A5, 0xFFC000, 0x5B9BD5, 0x70AD47]


def _tint(c, t):
    r, g, b = (c >> 16) & 255, (c >> 8) & 255, c & 255
    return (int(r + (255 - r) * t) << 16) | (int(g + (255 - g) * t) << 8) | int(b + (255 - b) * t)


def _shade(c, t):
    r, g, b = (c >> 16) & 255, (c >> 8) & 255, c & 255
    return (int(r * (1 - t)) << 16) | (int(g * (1 - t)) << 8) | int(b * (1 - t))


STYLE_VARIANTS = ["Colored Outline", "Colored Fill", "Colored Fill, Light Outline",
                  "Subtle Effect", "Moderate Effect", "Intense Effect"]


def style_spec(variant, accent):
    """(fill, outline, text colour, shadow) for a shape style."""
    a = accent
    if variant == 0:
        return 0xFFFFFF, a, 0x000000, False
    if variant == 1:
        return a, _shade(a, 0.3), 0xFFFFFF, False
    if variant == 2:
        return a, 0xFFFFFF, 0xFFFFFF, False
    if variant == 3:
        return _tint(a, 0.8), a, _shade(a, 0.3) if a else 0x000000, False
    if variant == 4:
        return _tint(a, 0.35), _shade(a, 0.2), 0xFFFFFF, True
    return a, a, 0xFFFFFF, True


