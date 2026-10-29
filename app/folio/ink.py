"""Draw tab: pens, highlighter and eraser. Strokes become line shapes on the
page (pen: on top of the text; highlighter: translucent, behind it)."""
import math

from gi.repository import Gdk, GLib

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
WP = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
WPS = "http://schemas.microsoft.com/office/word/2010/wordprocessingShape"

PENS = {
    "pen": {"color": 0x000000, "width": 50, "alpha": 0},
    "pen2": {"color": 0xC00000, "width": 100, "alpha": 0},
    "highlighter": {"color": 0xFFFF00, "width": 500, "alpha": 50},
}


class InkMode:
    def __init__(self, win):
        self.win = win
        self.tool = None             # 'pen', 'pen2', 'highlighter', 'eraser'
        self.points = []
        self._n = 0
        # a tool of the view: it gets the mouse before the text does
        win.engine.view.tools.append(self)

    @property
    def active(self):
        return self.tool is not None

    def begin(self, tool):
        self.tool = tool
        self.points = []
        w = self.win.engine.view.get_window()
        if w is not None:
            name = "cell" if tool == "eraser" else "pencil"
            try:
                w.set_cursor(Gdk.Cursor.new_from_name(w.get_display(), name) or
                             Gdk.Cursor.new_from_name(w.get_display(), "crosshair"))
            except Exception:
                pass
        self.win.status.flash("Draw on the page. Esc or Select returns to typing."
                              if tool != "eraser" else "Click or drag over ink to erase it.")
        if hasattr(self.win, "draw_buttons"):
            for k, b in self.win.draw_buttons.items():
                b.apply_state("true" if k == tool else "false")

    def stop(self):
        self.tool = None
        self.points = []
        w = self.win.engine.view.get_window()
        if w is not None:
            w.set_cursor(None)
        if hasattr(self.win, "draw_buttons"):
            for k, b in self.win.draw_buttons.items():
                b.apply_state("true" if k == "select" else "false")
        self.win.engine.view.queue_draw()

    def set_pen(self, tool, color=None, width=None):
        if color is not None:
            PENS[tool]["color"] = color
        if width is not None:
            PENS[tool]["width"] = width
        self.begin(tool)

    # ------------------------------------------------------------ events
    def press(self, ev):
        if ev.button != 1:
            return False
        if self.tool == "eraser":
            self._erase_at(ev.x, ev.y)
        else:
            self.points = [(ev.x, ev.y)]
        return True

    def motion(self, ev):
        view = self.win.engine.view
        if not (ev.state & Gdk.ModifierType.BUTTON1_MASK):
            return False
        if self.tool == "eraser":
            self._erase_at(ev.x, ev.y)
        elif self.points:
            lx, ly = self.points[-1]
            if math.hypot(ev.x - lx, ev.y - ly) >= 2:
                self.points.append((ev.x, ev.y))
                view.queue_draw()
        return True

    def release(self, ev):
        if ev.button != 1:
            return False
        if self.tool != "eraser" and len(self.points) >= 2:
            pts = list(self.points)
            tool = self.tool
            GLib.idle_add(lambda: (self._create(tool, pts), False)[1])
        self.points = []
        return True

    def draw(self, cr):
        if len(self.points) < 2 or self.tool == "eraser":
            return
        p = PENS[self.tool]
        c = p["color"]
        z = self.win.engine.view.get_zoom() or 1.0
        cr.set_source_rgba(((c >> 16) & 255) / 255.0, ((c >> 8) & 255) / 255.0,
                           (c & 255) / 255.0, 1 - p["alpha"] / 100.0)
        cr.set_line_width(max(1.0, p["width"] / 2540.0 * 96 * z))
        cr.set_line_cap(1)
        cr.set_line_join(1)
        cr.move_to(*self.points[0])
        for pt in self.points[1:]:
            cr.line_to(*pt)
        cr.stroke()
        return False

    # ------------------------------------------------------------ shapes
    def _create(self, tool, pts):
        """The stroke as a freeform shape on its page (points -> EMU)."""
        v = self.win.engine.view
        ed = self.win.engine.ed
        hit = [v.page_at(x, y) for x, y in pts]
        hit = [h for h in hit if h is not None and h[0] == hit[0][0]] if hit and hit[0] else []
        if len(hit) < 2:
            return
        pg = hit[0][0]
        xs, ys = [h[1] for h in hit], [h[2] for h in hit]
        x0, y0 = min(xs), min(ys)
        w, h = max(1.0, max(xs) - x0), max(1.0, max(ys) - y0)
        p = PENS[tool]
        emu = 12700
        path = "".join('<a:%s><a:pt x="%d" y="%d"/></a:%s>' % (
            "moveTo" if i == 0 else "lnTo", int((x - x0) * emu), int((y - y0) * emu),
            "moveTo" if i == 0 else "lnTo") for i, (x, y) in enumerate(zip(xs, ys)))
        alpha = ('<a:alpha val="%d"/>' % ((100 - p["alpha"]) * 1000)) if p["alpha"] else ""
        width_emu = int(p["width"] * 360)            # mm100 -> EMU
        self._n += 1
        xml = ('<w:r xmlns:w="%s" xmlns:wp="%s" xmlns:a="%s" xmlns:wps="%s"><w:rPr><w:noProof/></w:rPr>'
               '<w:drawing><wp:anchor distT="0" distB="0" distL="0" distR="0" simplePos="0" '
               'relativeHeight="{Z}" behindDoc="%d" locked="0" layoutInCell="1" allowOverlap="1">'
               '<wp:simplePos x="0" y="0"/><wp:positionH relativeFrom="page"><wp:posOffset>{X}</wp:posOffset></wp:positionH>'
               '<wp:positionV relativeFrom="page"><wp:posOffset>{Y}</wp:posOffset></wp:positionV>'
               '<wp:extent cx="%d" cy="%d"/><wp:effectExtent l="0" t="0" r="0" b="0"/><wp:wrapNone/>'
               '<wp:docPr id="{ID}" name="Ink {ID}"/><wp:cNvGraphicFramePr/>'
               '<a:graphic><a:graphicData uri="%s"><wps:wsp><wps:cNvSpPr/><wps:spPr>'
               '<a:xfrm><a:off x="0" y="0"/><a:ext cx="%d" cy="%d"/></a:xfrm>'
               '<a:custGeom><a:avLst/><a:gdLst/><a:ahLst/><a:cxnLst/><a:rect l="0" t="0" r="r" b="b"/>'
               '<a:pathLst><a:path w="%d" h="%d" fill="none">%s</a:path></a:pathLst></a:custGeom>'
               '<a:noFill/><a:ln w="%d" cap="rnd"><a:solidFill><a:srgbClr val="%06X">%s</a:srgbClr></a:solidFill>'
               '<a:round/></a:ln></wps:spPr><wps:bodyPr/></wps:wsp></a:graphicData></a:graphic></wp:anchor>'
               '</w:drawing></w:r>'
               % (W, WP, A, WPS, 1 if tool == "highlighter" else 0, int(w * emu), int(h * emu), WPS,
                  int(w * emu), int(h * emu), int(w * emu), int(h * emu), path, width_emu,
                  p["color"] & 0xFFFFFF, alpha))
        if ed.insert_anchor_xml(xml, pg, x0, y0):
            ed.deselect_object()
            v.document_changed()

    def _erase_at(self, x, y):
        """Delete the ink stroke under the pointer."""
        v = self.win.engine.view
        ed = self.win.engine.ed
        hit = v.page_at(x, y)
        if hit is None or not ed.select_object_at(*hit):
            return
        if 'name="Ink ' in (ed.selected_drawing_xml() or ""):
            ed.object_delete()
            v.document_changed()
        else:
            ed.click(hit[0], hit[1], hit[2], False)

    def key(self, event):
        if self.active and event.keyval == Gdk.KEY_Escape:
            self.stop()
            return True
        return False


def _seg_dist(px, py, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    if dx == dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / float(dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def _has_name(m, name):
    dp = m.getDrawPage()
    for i in range(dp.getCount()):
        try:
            if dp.getByIndex(i).Name == name:
                return True
        except Exception:
            pass
    return False


def _shape_info(sh):
    """Page and points of an ink stroke loaded from a file."""
    try:
        poly = sh.PolyPolygon
        coords = [(p.X, p.Y) for p in poly[0]]
        xs = [c[0] for c in coords]
        ys = [c[1] for c in coords]
        page = sh.AnchorPageNo or 1
        return page, (min(xs), min(ys), max(xs), max(ys)), coords
    except Exception:
        return None


def _simplify(pts, tol):
    """Drop points closer than tol to the previous kept point."""
    out = [pts[0]]
    for p in pts[1:]:
        if math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) >= tol:
            out.append(p)
    if out[-1] != pts[-1]:
        out.append(pts[-1])
    return out
