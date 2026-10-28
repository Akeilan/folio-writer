"""3-D Rotation perspective presets drawn foreshortened (W2-09), checked on the rendered page."""
import os
import sys
import tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "app"))
import folio_core  # noqa: E402
import cairo  # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else " | " + str(detail)))
    if not cond:
        FAILS.append(name)


tmp = tempfile.mkdtemp()
png = os.path.join(tmp, "p.png")
s = cairo.ImageSurface(cairo.FORMAT_RGB24, 200, 200)
c = cairo.Context(s)
c.set_source_rgb(0.1, 0.4, 0.2)
c.paint()
s.write_to_png(png)
tpl = os.path.join(HERE, "..", "share", "templates", "Normal-Letter.docx")


def picture_rows(prst):
    ed = folio_core.Editor.open(tpl)
    ed.insert_picture(png)
    ed.object_effect("a:scene3d", '<a:scene3d><a:camera prst="%s"/><a:lightRig rig="threePt" dir="t"/></a:scene3d>' % prst)
    w, h, stride, data = ed.render_page(0, 1.0, False, False)
    rows = {}
    for y in range(h):
        n = 0
        for x in range(w):
            i = y * stride + x * 4
            if data[i + 1] > 70 and data[i + 2] < 60 and data[i] < 90:
                n += 1
        if n:
            rows[y] = n
    return rows


def picture_columns(prst):
    """Height of the dark picture in each pixel column of page 1."""
    ed = folio_core.Editor.open(tpl)
    ed.insert_picture(png)
    if prst:
        ed.object_effect("a:scene3d", '<a:scene3d><a:camera prst="%s"/><a:lightRig rig="threePt" dir="t"/></a:scene3d>' % prst)
    w, h, stride, data = ed.render_page(0, 1.0, False, False)
    cols = {}
    for x in range(w):
        n = 0
        for y in range(h):
            i = y * stride + x * 4
            b, g, r = data[i], data[i + 1], data[i + 2]
            if g > 70 and r < 60 and b < 90:
                n += 1
        if n:
            cols[x] = n
    return cols


flat = picture_columns(None)
check("flat picture drawn", flat and max(flat.values()) > 50, len(flat))
fh = list(flat.values())
check("flat: edges the same height", abs(fh[0] - fh[-1]) <= 2, (fh[0], fh[-1]))
for prst in ("perspectiveLeft", "perspectiveRight", "perspectiveAbove"):
    cols = picture_columns(prst)
    xs = sorted(cols)
    check(prst + " drawn", len(xs) > 20, len(xs))
    if len(xs) > 20:
        left, right = cols[xs[2]], cols[xs[-3]]
        if prst == "perspectiveAbove":
            rows = picture_rows(prst)
            ys = sorted(rows)
            top, bot = rows[ys[2]], rows[ys[-3]]
            check(prst + ": top and bottom differ in width (foreshortened)", abs(top - bot) > 6, (top, bot))
        else:
            check(prst + ": near edge taller than far edge", abs(left - right) > 6, (left, right))
            if prst == "perspectiveLeft":
                check(prst + ": the right side recedes", left > right, (left, right))
            else:
                check(prst + ": the left side recedes", right > left, (left, right))
print("DONE failures:", len(FAILS))
sys.exit(1 if FAILS else 0)
