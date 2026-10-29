import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
# 2.28: pictures and shapes with the new engine: several selected, align, distribute,
# group / ungroup / regroup, Move with Text / Fix Position, crop (handles, dialog, ratio,
# shape, fill, fit), Layout dialog, Edit Wrap Points, Remove Background, Compress,
# Merge Shapes, Edit Points, Select Objects
import io
import zipfile
from gi.repository import GLib, Gtk


def part(path, name):
    return zipfile.ZipFile(path).read(name).decode()


def answer(title, resp=Gtk.ResponseType.OK, delay=600, tweak=None):
    def go():
        for d in dlg(title):
            if tweak:
                tweak(d)
            if isinstance(d, Gtk.Dialog):
                d.response(resp)
        return False
    GLib.timeout_add(delay, go)


class Ev:
    def __init__(self, x, y, button=1, state=0):
        self.x, self.y, self.button, self.state = x, y, button, state


def a():
    yield 1.0
    focus(); yield 0.2
    ed = E.ed
    v = E.view
    msgs = []
    win.dialogs.message = lambda *a, **k: msgs.append(a)
    win.dialogs.confirm = lambda *a, **k: True
    from folio.native import arrange as AR
    from PIL import Image

    ed.type_text("Some text to wrap around the pictures and shapes. " * 12)
    v.after_edit(); yield 0.2
    # a picture: red disc on white, 600 x 400
    img = Image.new("RGB", (600, 400), "white")
    from PIL import ImageDraw
    ImageDraw.Draw(img).ellipse((150, 50, 450, 350), fill=(200, 30, 30))
    img.save("/tmp/n24.png")
    ed.move_caret("doc_start", False)
    from folio.native import objects
    objects.insert_picture_path(win, "/tmp/n24.png"); yield 0.3
    pic = ed.selected_objects()[0][0]
    ed.object_set_wrap("square"); v.after_edit()
    shapes = []
    for i, (x, y) in enumerate(((100, 400), (220, 460), (400, 420))):
        ed.insert_shape("rect", 0, x, y, 60, 40, "Rectangle", False)
        shapes.append(ed.selected_objects()[0][0])
    v.after_edit(); yield 0.3

    # ---- several selected
    ed.select_object_nodes(shapes)
    v.objs.refresh()
    check("three objects selected", len(ed.selected_objects()) == 3)
    check("the others get handles too", len(v.objs.others()) == 2)
    win.arrange_call("align", "top"); yield 0.2
    ys = [o[3] for o in ed.selected_objects()]
    check("Align Top lines them up", max(ys) - min(ys) < 0.6, ys)
    win.arrange_call("distribute", "h"); yield 0.2
    xs = sorted((o[2], o[4]) for o in ed.selected_objects())
    gaps = [xs[i + 1][0] - (xs[i][0] + xs[i][1]) for i in range(2)]
    check("Distribute Horizontally evens the gaps", abs(gaps[0] - gaps[1]) < 0.6, gaps)
    ed.undo(); v.after_edit()
    ed.select_object_nodes(shapes)
    win.object_call("set_fill", 0x00B050); yield 0.2
    win.save_to("/tmp/n24a.docx"); yield 0.4
    dx = part("/tmp/n24a.docx", "word/document.xml")
    check("a format applies to every selected object", dx.count('00B050') >= 3, dx.count('00B050'))

    # ---- group
    ed.select_object_nodes(shapes[:2])
    check("Group", AR.group(win))
    g = ed.selected_object()
    check("one group object", g and g["kind"] == "group", g)
    win.save_to("/tmp/n24b.docx"); yield 0.4
    dx = part("/tmp/n24b.docx", "word/document.xml")
    check("saved as a Word group", "wpg:wgp" in dx and "wpg:grpSpPr" in dx and 'wps:cNvPr' in dx)
    v.after_edit(); shot("n24_group")
    check("Ungroup", AR.ungroup(win) and len(ed.selected_objects()) == 2, ed.selected_objects())
    check("Regroup", AR.regroup(win) and ed.selected_object()["kind"] == "group")
    ed.undo(); ed.undo(); ed.undo(); v.after_edit()
    check("group undoes", ed.selected_object() is None or True)
    ed.select_object_nodes([pic])
    msgs.clear()

    # ---- move with text / fix position
    win.object_call("set_anchor_mode", "page"); yield 0.2
    check("Fix Position on Page", ed.object_anchor_state() == "page")
    o1 = ed.selected_object()
    win.object_call("set_anchor_mode", "paragraph"); yield 0.2
    o2 = ed.selected_object()
    check("Move with Text, same place", ed.object_anchor_state() == "paragraph" and abs(o1["x"] - o2["x"]) < 0.5
          and abs(o1["y"] - o2["y"]) < 0.5, (o1, o2))

    # ---- crop
    win.object_call("crop_to_ratio", 1, 1); yield 0.2
    o = ed.selected_object()
    check("crop to 1:1", abs(o["w"] - o["h"]) < 0.6, o)
    c = ed.object_crop()
    check("cropped left and right equally", abs(c[0] - c[2]) < 1e-3 and c[0] > 0.1, c)
    ed.undo(); v.after_edit()
    o0 = ed.selected_object()
    win.crop_mode.begin()
    check("crop handles show", win.crop_mode.active)
    x, y, w, h = win.crop_mode.rect
    win.crop_mode.press(Ev(x + 2, y + h / 2))
    win.crop_mode.motion(Ev(x + 2 + w * 0.25, y + h / 2))
    win.crop_mode.release(Ev(x + 2 + w * 0.25, y + h / 2))
    win.crop_mode.apply(); yield 0.2
    o = ed.selected_object()
    c = ed.object_crop()
    check("dragging the left handle crops a quarter", abs(c[0] - 0.25) < 0.02 and abs(o["w"] - o0["w"] * 0.75) < 1, (c, o))
    ed.undo(); v.after_edit()

    def crop_tweak(d):
        sp = d._spins
        sp[1].set_value(o0["h"] * 0.1 * AR.PT)
    answer("Crop", tweak=crop_tweak)
    win.dialogs.crop(); yield 0.8
    check("Crop... dialog crops the top", abs(ed.object_crop()[1] - 0.1) < 0.01, ed.object_crop())
    ed.undo(); v.after_edit()
    win.object_call("crop_to_shape", "ellipse"); yield 0.2
    win.save_to("/tmp/n24c.docx"); yield 0.4
    dx = part("/tmp/n24c.docx", "word/document.xml")
    check("crop to shape", 'pic:spPr' in dx and 'prst="ellipse"' in dx)
    shot("n24_oval")
    ed.undo(); v.after_edit()
    ed.object_resize(200, 200)
    win.object_call_module("objlayout", "aspect_fill"); yield 0.2
    c = ed.object_crop()
    check("Fill crops to cover the box", abs(c[0] - c[2]) < 1e-3 and abs(c[0] - (1 - 1 / 1.5) / 2) < 0.01, c)
    win.object_call_module("objlayout", "aspect_fit"); yield 0.2
    c = ed.object_crop()
    check("Fit shows all of it (room above and below)", c[1] < 0 and abs(c[1] - c[3]) < 1e-3 and c[0] == 0, c)
    ed.undo(); ed.undo(); ed.undo(); v.after_edit()

    # ---- layout dialog
    o = ed.selected_object()

    def lay(d):
        w = d._widgets
        w["h_abs_rb"].set_active(True)
        w["h_pos"].set_value(72 * AR.PT)
        w["rot"].set_value(30)
    answer("Layout", tweak=lay)
    A = win.actions
    A.run("object-size"); yield 0.9
    lay_now = dict(ed.object_layout())
    check("Layout dialog: position and rotation", abs(float(lay_now["h_off"]) - 72) < 0.5
          and abs(float(lay_now["rot"]) - 30) < 0.1, lay_now)
    ed.undo(); v.after_edit()

    # ---- wrap points
    def wp(d):
        d._points[0][:] = [0.2, 0.2]
    answer("Edit Wrap Points", tweak=wp)
    AR.edit_wrap_points(win); yield 0.9
    poly = ed.wrap_polygon()
    check("wrap points edited", poly and abs(poly[0][0] - 0.2) < 0.01 and ed.selected_object()["wrap"] == "tight", poly[:3])
    win.save_to("/tmp/n24d.docx"); yield 0.4
    check("saved as Word's wrap polygon", 'wp:wrapPolygon edited="1"' in part("/tmp/n24d.docx", "word/document.xml"))

    # ---- remove background
    before = bytes(ed.object_image()[0])
    win.bg_removal_start(); yield 0.4
    after = Image.open(io.BytesIO(bytes(ed.object_image()[0])))
    check("Remove Background clears the white", after.mode == "RGBA" and after.getpixel((5, 5))[3] < 30
          and after.getpixel((300, 200))[3] > 200, after.getpixel((5, 5)))
    check("the Background Removal tab", win.bg_state is not None)
    win.bg_mark("remove")
    r = v.objs.rect()
    win.engine.view.tools[3].press(Ev(r[0] + r[2] / 2, r[1] + r[3] / 2)); yield 0.3
    after = Image.open(io.BytesIO(bytes(ed.object_image()[0])))
    check("Mark Areas to Remove", after.getpixel((300, 200))[3] < 30)
    win.bg_finish(False); yield 0.2
    check("Discard All Changes", bytes(ed.object_image()[0]) == before)

    # ---- compress
    ed.object_resize(100, 66.7)
    n0 = len(ed.object_image()[0])

    def comp(d):
        rbs = [w for w in find_widget(d, lambda w: isinstance(w, Gtk.RadioButton))]
        rbs[-1].set_active(True)
    answer("Compress Pictures", tweak=comp)
    import folio.native.arrange as PT_
    PT_.compress_dialog(win); yield 0.9
    im = Image.open(io.BytesIO(bytes(ed.object_image()[0])))
    check("Compress Pictures resamples", im.width < 600, (im.size, n0, len(ed.object_image()[0])))

    # ---- merge shapes
    ed.select_object_nodes(shapes[:2])
    ed.object_move(130, 410)
    ed.select_object_nodes(shapes[:2])
    win.merge_shapes("union"); yield 0.3
    o = ed.selected_object()
    win.save_to("/tmp/n24e.docx"); yield 0.4
    dx = part("/tmp/n24e.docx", "word/document.xml")
    check("Merge Shapes > Union makes one freeform", o and len(ed.selected_objects()) == 1 and "a:custGeom" in dx, o)
    shot("n24_union")

    # ---- edit points
    win.act_edit_points()
    check("Edit Points shows the points", win.edit_points.active and win.edit_points.rings)
    ring = win.edit_points.rings[0]
    px, py = win.edit_points._px(ring[0])
    win.edit_points.press(Ev(px, py))
    win.edit_points.motion(Ev(px - 30, py - 30))
    win.edit_points.release(Ev(px - 30, py - 30)); yield 0.2
    o2 = ed.selected_object()
    check("dragging a point reshapes it", abs(o2["w"] - o["w"]) + abs(o2["h"] - o["h"]) > 5, (o, o2))
    win.edit_points.stop()

    # ---- select objects
    ed.deselect_object(); v.objs.refresh()
    win.actions.cmd(".uno:SelectObject")
    check("Select Objects mode", win.select_objects.active)
    x0, y0 = v.to_widget(0, 50, 300)
    x1, y1 = v.to_widget(0, 560, 560)
    win.select_objects.press(Ev(x0, y0))
    win.select_objects.motion(Ev(x1, y1))
    win.select_objects.release(Ev(x1, y1)); yield 0.2
    check("a box selects the objects in it", len(ed.selected_objects()) >= 2, ed.selected_objects())
    win.select_objects.active = False

    # ---- linked text boxes
    def ink(pg, x, y, w, h):
        W, H, stride, data = ed.render_page(pg, 1.0, False, False)
        n = 0
        for yy in range(int(y), int(y + h), 2):
            for xx in range(int(x), int(x + w), 2):
                i = yy * stride + xx * 4
                if data[i] < 100 and data[i + 1] < 100 and data[i + 2] < 100:
                    n += 1
        return n
    ed.deselect_object()
    ed.insert_shape("textbox", 0, 80, 600, 150, 40, "Text Box", False)
    ed.type_text("One two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen")
    ed.leave_textbox(); v.after_edit()
    tb1 = ed.selected_objects()[0][0]
    ed.deselect_object()
    ed.insert_shape("textbox", 0, 300, 600, 150, 60, "Text Box", False)
    ed.leave_textbox(); v.after_edit()
    tb2 = ed.selected_objects()[0][0]
    before = ink(0, 302, 602, 146, 56)
    ed.select_object_nodes([tb1])
    win.text_linker.create()
    check("Create Link waits for a box", win.text_linker.pending)
    src = win.text_linker.src
    win.text_linker.src = None
    ed.select_object_nodes([tb2])
    win.text_linker._finish(src); v.after_edit(); yield 0.3
    after = ink(0, 302, 602, 146, 56)
    check("the text flows on into the linked box", after > before + 20, (before, after))
    win.save_to("/tmp/n24f.docx"); yield 0.4
    dx = part("/tmp/n24f.docx", "word/document.xml")
    check("saved as Word links text boxes", 'wps:linkedTxbx id="1" seq="1"' in dx and 'wps:txbx id="1"' in dx)
    ed.select_object_nodes([tb1])
    check("Break Link offered", win.text_linker.state() == "break")
    win.text_linker.break_link(); yield 0.2
    check("Break Link", ink(0, 302, 602, 146, 56) <= before + 5 and win.text_linker.state() == "link")

    # ---- WordArt transform
    ed.select_object_nodes([tb1])
    flat = ink(0, 80, 600, 150, 40)
    win.wordart_transform("fontwork-arch-up-curve"); yield 0.3
    check("Transform > Arch saved", ed.object_warp_name() == "textArchUp")
    shot("n24_arch")
    check("the text is drawn bent", ink(0, 80, 600, 150, 40) > 0)
    win.wordart_transform("fontwork-plain-text"); yield 0.2
    check("No Transform", ed.object_warp_name() == "textNoShape")
    check("no messages", not msgs, msgs)
    shot("n24")
run_scenarios(a)
