import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
# W4-01: 3D models in documents. A glTF model comes in, is drawn flat-shaded at the angle it is
# turned to, turns from the views gallery and to exact angles, and travels in the .docx the way
# Word keeps one: a .glb part with a picture of the current view, in an AlternateContent whose
# Choice is am3d:model3d and whose Fallback is a plain picture.
import os
import re
import tempfile
import zipfile

from gi.repository import GLib, Gtk
from folio import model3d, model3dui

TMP = tempfile.mkdtemp(prefix="n48-")
GLB = os.path.join(TMP, "Cube.glb")


def rels(path):
    z = zipfile.ZipFile(path)
    return z.read("word/_rels/document.xml.rels").decode("utf-8", "replace")


def doc_xml(path):
    return zipfile.ZipFile(path).read("word/document.xml").decode("utf-8", "replace")


def a():
    yield 1.0
    ed = E.ed
    with open(GLB, "wb") as fh:
        fh.write(model3d.cube_glb())
    check("the test model is a glTF binary", open(GLB, "rb").read(4) == b"glTF")
    mesh = model3d.Mesh(open(GLB, "rb").read())
    check("it reads as triangles", len(mesh.tris) >= 12, len(mesh.tris))

    # ---------------------------------------------------------------- insert
    fresh()
    ed.type_text("A model below:\n"); E.view.after_edit(); yield 0.3
    part = model3dui.insert(win, GLB); yield 1.0
    check("Insert > 3D Models puts the model in", part and part.endswith(".glb"), part)
    o = ed.selected_object()
    check("it is selected, and as wide as it is tall", o and abs(o["w"] - o["h"]) < 1.0, o and (o["w"], o["h"]))
    check("the document knows it is a 3D model", model3dui.selected(win) is not None)
    got = model3dui.selected(win)
    check("at the angle it was put in at", got and max(abs(x - y) for x, y in zip(got[1], model3dui.DEFAULT_ROT)) < 0.01,
          got and got[1])
    check("and the model itself can be read back out of the document",
          bytes(ed.model3d_glb() or b"")[:4] == b"glTF", bytes(ed.model3d_glb() or b"")[:4])
    xml = ed.selected_drawing_xml() or ""
    check("the drawing is Word's 3D model, not a picture",
          'uri="http://schemas.microsoft.com/office/drawing/2017/model3d"' in xml and "am3d:model3d" in xml,
          xml[:160])
    check("with the picture of this view in its raster", "am3d:raster" in xml and "am3d:blip" in xml)
    check("and the rotation written as DrawingML angles",
          re.search(r'am3d:rot ax="(-?\d+)" ay="(-?\d+)"', xml) is not None, xml[:200])

    # it draws: the page shows the model, not a blank box
    shot("n48_model")
    img = ed.object_image()
    check("Page draws the picture of the model", img and bytes(img[0])[:4] == b"\x89PNG",
          img and (bytes(img[0])[:4], img[1]))

    # ---------------------------------------------------------------- turning
    before = bytes((ed.object_image() or (b"",))[0])
    new = model3dui.view(win, "left"); yield 0.8
    check("3D Model Views > Left turns it", new and abs(new[1] - 90.0) < 0.01, new)
    after = bytes((ed.object_image() or (b"",))[0])
    check("and draws it again from there", after and after != before, (len(before), len(after)))
    xml = ed.selected_drawing_xml() or ""
    m = re.search(r'am3d:rot ax="(-?\d+)" ay="(-?\d+)" az="(-?\d+)"', xml)
    check("the file records the new angle", m and int(m.group(2)) == 90 * 60000, m and m.groups())
    check("both branches show the same view",
          len(set(re.findall(r'(?:am3d:blip|a:blip) r:embed="([^"]+)"', xml))) == 1,
          re.findall(r'(?:am3d:blip|a:blip) r:embed="([^"]+)"', xml))

    for name, want in (("top", (90.0, 0.0, 0.0)), ("above-front-right", (25.0, -35.0, 0.0))):
        got = model3dui.view(win, name); yield 0.5
        check("3D Model Views > %s" % name, got and max(abs(x - y) for x, y in zip(got, want)) < 0.01, got)

    got = model3dui.nudge(win, "right"); yield 0.5
    check("a step to the right turns it 15 degrees", got and abs(got[1] - (-35.0 + 15.0)) < 0.01, got)
    got = model3dui.nudge(win, "down"); yield 0.5
    check("and a step down tips it", got and abs(got[0] - 40.0) < 0.01, got)
    check("an unknown step says so rather than turning it", model3dui.nudge(win, "sideways") is None)

    # exact angles, through the dialog: fill the three boxes in and press OK
    def answer_turn():
        for wd in Gtk.Window.list_toplevels():
            if wd.get_visible() and (wd.get_title() or "") == "Turn 3D Model":
                sp = getattr(wd, "spins", None)
                check("the Turn dialog has a box for each axis", sp and set(sp) == {"x", "y", "z"}, sp)
                if sp:
                    for k, v in (("x", 10), ("y", -20), ("z", 30)):
                        sp[k].set_value(v)
                wd.response(Gtk.ResponseType.OK)
                return False
        return True
    GLib.timeout_add(300, answer_turn)
    turned = model3dui.turn_dialog(win); yield 1.2
    check("Turn... takes exact angles", turned and max(abs(a - b) for a, b in zip(turned, (10.0, -20.0, 30.0))) < 0.01,
          turned)
    got = model3dui.reset(win); yield 0.5
    check("Reset 3D Model puts it back", got and max(abs(x - y) for x, y in zip(got, model3dui.DEFAULT_ROT)) < 0.01, got)

    # ---------------------------------------------------------------- the .docx
    out = os.path.join(TMP, "model.docx")
    check("saved", win.save_to(out)); yield 1.0
    z = zipfile.ZipFile(out)
    glbs = [n for n in z.namelist() if n.endswith(".glb")]
    check("the .docx carries the model as a .glb part", len(glbs) == 1, z.namelist())
    check("byte for byte what went in", z.read(glbs[0]) == open(GLB, "rb").read(), len(z.read(glbs[0])))
    ct = z.read("[Content_Types].xml").decode("utf-8", "replace")
    check("with the content type Word uses", 'Extension="glb"' in ct and "model/gltf-binary" in ct,
          [x for x in ct.split("<") if "glb" in x])
    r = rels(out)
    check("related as a 3D model", "office/2017/06/relationships/model3d" in r,
          [x for x in r.split("<") if "model" in x])
    dx = doc_xml(out)
    check("the document holds the model drawing", "am3d:model3d" in dx and "mc:Fallback" in dx)
    check("and a picture beside it for readers that have no 3D", "pic:pic" in dx)
    pngs = [n for n in z.namelist() if n.endswith(".png")]
    check("the picture of the view travels too", len(pngs) >= 1, pngs)

    # opened again, it is still a model that can be turned
    win.open_file(out); yield 2.0
    ed = win.engine.ed
    objs = ed.objects_list()
    check("the model is there when the file is opened again", objs, objs[:1])
    if objs:
        o0 = objs[0]
        if isinstance(o0, dict) and "node" in o0:
            ed.select_object_node(o0["node"])
        else:
            ed.select_object_at(o0.get("page", 0) if isinstance(o0, dict) else 0,
                                (o0.get("x", 10) if isinstance(o0, dict) else 100) + 5,
                                (o0.get("y", 10) if isinstance(o0, dict) else 150) + 5)
        yield 0.4
        got = model3dui.selected(win)
        check("still known as a 3D model", got is not None, got)
        check("with its model readable", bytes(win.engine.ed.model3d_glb() or b"")[:4] == b"glTF")
        turned = model3dui.view(win, "back"); yield 0.8
        check("and it turns again after a round trip", turned and abs(abs(turned[1]) - 180.0) < 0.01, turned)
    win.engine.ed.mark_saved()


run_scenarios(a)
