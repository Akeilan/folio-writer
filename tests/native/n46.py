import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
# K3-08: a diagram copied in Folio Cork pastes as an editable diagram; double-click opens it in
# Cork and each save there updates the picture; the saved document carries it.
import os
import shutil
import tempfile
import time
import zipfile

from gi.repository import Gdk, GdkPixbuf, Gtk
from folio import corkembed

DATA = os.path.join(TESTS, "data")
TMP = tempfile.mkdtemp(prefix="n46-")


class Ev:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def a():
    yield 1.0
    ed = E.ed
    v = E.view
    diag = open(os.path.join(DATA, "diagram.png"), "rb").read()
    cfg = os.path.join(TMP, "cfg")
    os.makedirs(cfg)
    os.environ["FOLIO_CONFIG_DIR"] = cfg
    with open(os.path.join(cfg, "clipboard.png"), "wb") as fh:
        fh.write(diag)
    ld = GdkPixbuf.PixbufLoader.new_with_type("png")
    ld.write(diag)
    ld.close()
    cb = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
    cb.set_image(ld.get_pixbuf()); yield 0.3
    ed.type_text("Diagram below:\n"); v.after_edit(); yield 0.2
    E.paste(); yield 0.6
    got = ed.object_image() if ed.selected_object() else None
    check("pasted as an editable diagram", bool(got) and corkembed.is_diagram(bytes(got[0])),
          got and len(got[0]))
    o0 = ed.selected_object()
    # a different picture of the same size pastes as an ordinary picture
    other = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, 928, 720)
    other.fill(0x30A050FF)
    cb.set_image(other); yield 0.3
    ed.deselect_object(); ed.move_caret("doc_end", False); v.after_move()
    E.paste(); yield 0.6
    g2 = ed.object_image() if ed.selected_object() else None
    check("another picture stays a plain picture", bool(g2) and not corkembed.is_diagram(bytes(g2[0])))
    E.ed.undo(); v.document_changed(); yield 0.3
    # double-click the diagram: Cork (a stand-in here) saves a wider picture
    fake = os.path.join(TMP, "fake-cork")
    shutil.copy(os.path.join(DATA, "fake_cork.py"), fake)
    os.chmod(fake, 0o755)
    os.environ["FOLIO_CORK"] = fake
    if o0:
        ed.deselect_object(); v.objs.refresh()
        wx, wy = v.to_widget(o0["page"], o0["x"] + o0["w"] / 2, o0["y"] + o0["h"] / 2)
        st = Gdk.ModifierType(0)
        v._press(v, Ev(type=Gdk.EventType.BUTTON_PRESS, x=wx, y=wy, button=1, state=st, time=0))
        v._press(v, Ev(type=Gdk.EventType._2BUTTON_PRESS, x=wx, y=wy, button=1, state=st, time=0))
        t0 = time.time()
        new = None
        while time.time() - t0 < 8:
            yield 0.3
            ed.select_object_node(ed.selected_objects()[0][0]) if ed.selected_objects() else None
            nodes = ed.selected_objects()
            img = ed.object_image() if nodes else None
            if img and corkembed.png_size(bytes(img[0])) == (600, 200):
                new = img
                break
        check("saving in Cork updates the diagram", new is not None and corkembed.is_diagram(bytes(new[0])))
        o1 = ed.selected_object()
        check("it takes the new proportions", o1 is not None and abs(o1["w"] / o1["h"] - 3.0) < 0.05,
              o1 and (o1["w"], o1["h"]))
    out = os.path.join(TMP, "diagram.docx")
    check("saved", win.save_to(out)); yield 0.6
    z = zipfile.ZipFile(out)
    check("the document carries the diagram",
          any(corkembed.is_diagram(z.read(n)) for n in z.namelist() if n.startswith("word/media/")))
    out2 = os.path.join(TMP, "diagram.doc")
    check("saved as .doc", win.save_to(out2)); yield 0.6
    check("the .doc carries it too", corkembed.CHUNK in open(out2, "rb").read())
    del os.environ["FOLIO_CORK"]
    E.ed.mark_saved()


run_scenarios(a)
