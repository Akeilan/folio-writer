"""Developer > Controls: content controls (rich text, plain text, picture,
check box, combo box, drop-down list, date picker), their Properties, and
the pickers that open when you click a drop-down or date control."""
import datetime

from gi.repository import Gdk, GLib, Gtk

from . import bridge, docapi
from .widgets import FDialog, grid
from .native import values
from . import modelapi

PLACEHOLDER = {"rich": "Click or tap here to enter text.",
               "plain": "Click or tap here to enter text.",
               "combo": "Choose an item.", "dropdown": "Choose an item.",
               "date": "Click or tap to enter a date.", "picture": "", "checkbox": ""}


def _native(win):
    from .native import controls
    return controls


def insert(win, kind):
    if _native(win):
        return _native(win).insert(win, kind)
    return


def _insert_placeholder_picture(m, cc):
    import os
    import tempfile
    try:
        from PIL import Image, ImageDraw
        img = Image.new("RGB", (240, 180), (242, 242, 242))
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, 239, 179], outline=(166, 166, 166))
        d.polygon([(70, 130), (105, 85), (125, 110), (150, 75), (180, 130)],
                  fill=(166, 166, 166))
        d.ellipse([150, 45, 170, 65], fill=(166, 166, 166))
        path = tempfile.mktemp(suffix=".png")
        img.save(path)
        rng = cc.getText().createTextCursorByRange(cc.getStart()) if hasattr(
            cc, "getText") else None
        vc = modelapi.view_cursor(m)
        if rng is not None:
            vc.gotoRange(rng, False)
        docapi.insert_picture(m, path)
        os.remove(path)
    except Exception as e:
        print("picture control:", e)


def control_at_cursor(m):
    """The content control the cursor is in, or None."""
    vc = modelapi.read_cursor(m)
    try:
        cc = vc.ContentControl
        if cc is not None:
            return cc
    except Exception:
        pass
    try:
        text = vc.getText()
        here = vc.getStart()
        para = text.createTextCursorByRange(here)
        para.gotoStartOfParagraph(False)
        para.gotoEndOfParagraph(True)
        en = para.createEnumeration()
        while en.hasMoreElements():
            p = en.nextElement()
            if not p.supportsService("com.sun.star.text.Paragraph"):
                continue
            pe = p.createEnumeration()
            while pe.hasMoreElements():
                r = pe.nextElement()
                if getattr(r, "TextPortionType", "") != "ContentControl":
                    continue
                cc = r.ContentControl
                try:
                    if text.compareRegionStarts(cc.getStart(), here) >= 0 and \
                            text.compareRegionEnds(cc.getEnd(), here) <= 0:
                        return cc
                except Exception:
                    continue
    except Exception:
        pass
    return None


def kind_of(cc):
    for k, prop in (("checkbox", "Checkbox"), ("combo", "ComboBox"), ("dropdown", "DropDown"),
                    ("date", "Date"), ("picture", "Picture"), ("plain", "PlainText")):
        try:
            if getattr(cc, prop):
                return k
        except Exception:
            pass
    return "rich"


def _items(cc):
    out = []
    try:
        for item in cc.ListItems:
            d = {p.Name: p.Value for p in item}
            out.append((d.get("DisplayText", ""), d.get("Value", "")))
    except Exception:
        pass
    return out


def _set_items(cc, items):
    import uno
    seq = tuple((values.prop("DisplayText", t), values.prop("Value", v)) for t, v in items)
    uno.invoke(cc, "setPropertyValue", ("ListItems", uno.Any(
        "[][]com.sun.star.beans.PropertyValue", seq)))




def properties(win):
    if _native(win):
        return _native(win).properties(win)
    return
