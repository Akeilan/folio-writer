"""Built-in cover pages and header / footer designs, as in the original's
galleries, plus saving the selection to those galleries."""
import datetime

from .native import values
from . import modelapi

MARK = "_CoverPage"
SHAPE = "CoverPageShape"

# name: accent, band (None / top / bottom / left / full), title colour on band,
# title size, uppercase, align
COVERS = [
    ("Simple", dict(accent=0x2F5496, band=None, size=40, caps=False, align="left")),
    ("Banded", dict(accent=0xC00000, band="bottom", size=36, caps=True, align="center")),
    ("Grid", dict(accent=0x375623, band="left", size=36, caps=False, align="left")),
    ("Facet", dict(accent=0x70AD47, band="left", size=40, caps=True, align="right")),
    ("Ion (Dark)", dict(accent=0x1F3864, band="full", size=44, caps=True, align="left")),
    ("Ion (Light)", dict(accent=0x4472C4, band=None, size=44, caps=True, align="left")),
    ("Motion", dict(accent=0xED7D31, band="top", size=36, caps=False, align="left")),
    ("Retrospect", dict(accent=0x5B9BD5, band="bottom", size=40, caps=True, align="center")),
    ("Semaphore", dict(accent=0xA5A5A5, band="top", size=40, caps=True, align="left")),
    ("Sideline", dict(accent=0x4472C4, band=None, size=40, caps=False, align="left",
                      rule=True)),
    ("Slice (Dark)", dict(accent=0x262626, band="full", size=44, caps=True, align="left")),
    ("Whisp", dict(accent=0x7F7F7F, band=None, size=36, caps=False, align="left",
                   rule=True)),
]
ALIGN = {"left": 0, "right": 1, "center": 3}


def _props(win, m):
    p = modelapi.doc_properties(m)
    return (p["title"] or "Document title", p["subject"] or "Document subtitle",
            p["author"] or win.app.user_name(),
            datetime.date.today().strftime("%B %-d, %Y"))


def remove_cover(m):
    bms = m.getBookmarks()
    found = False
    if bms.hasByName(MARK):
        bm = bms.getByName(MARK)
        a = bm.getAnchor()
        text = a.getText()
        c = text.createTextCursorByRange(a.getStart())
        c.gotoRange(a.getEnd(), True)
        # with the paragraph that ends the cover page
        c.gotoEndOfParagraph(True)
        nxt = text.createTextCursorByRange(c.getEnd())
        if nxt.gotoNextParagraph(False):
            c.gotoRange(nxt.getStart(), True)
        text.removeTextContent(bm)
        c.setString("")
        try:
            c.BreakType = values.enum("com.sun.star.style.BreakType", "NONE")
        except Exception:
            pass
        found = True
    dp = m.getDrawPage()
    for i in reversed(range(dp.getCount())):
        try:
            o = dp.getByIndex(i)
            if (o.Name or "").startswith(SHAPE):
                dp.remove(o)
                found = True
        except Exception:
            pass
    # the first paragraph of the document took the page break: no more
    try:
        first = m.getText().createEnumeration().nextElement()
        if getattr(first.BreakType, "value", "") == "PAGE_BEFORE":
            first.BreakType = values.enum("com.sun.star.style.BreakType", "NONE")
    except Exception:
        pass
    return found


def _band(m, spec, ps):
    band = spec.get("band")
    if not band:
        return None
    W, H = ps.Width, ps.Height
    x, y, w, h = {"top": (0, 0, W, int(H * 0.38)), "bottom": (0, int(H * 0.72), W, int(H * 0.28)),
                  "left": (0, 0, int(W * 0.08), H), "full": (0, 0, W, H)}[band]
    s = m.createInstance("com.sun.star.drawing.RectangleShape")
    s.AnchorType = values.enum("com.sun.star.text.TextContentAnchorType", "AT_PAGE")
    m.getDrawPage().add(s)
    s.AnchorPageNo = 1
    s.Size = values.struct("com.sun.star.awt.Size", Width=w, Height=h)
    s.HoriOrient, s.HoriOrientRelation, s.HoriOrientPosition = 0, 7, x
    s.VertOrient, s.VertOrientRelation, s.VertOrientPosition = 0, 7, y
    s.FillColor = spec["accent"]
    s.LineStyle = values.enum("com.sun.star.drawing.LineStyle", "NONE")
    s.TextWrap = values.enum("com.sun.star.text.WrapTextMode", "THROUGH")
    s.Opaque = False
    s.Name = SHAPE + "1"
    return band


def _native(win):
    return getattr(getattr(win, "engine", None), "native", False)


def remove_current(win):
    """Remove Current Cover Page."""
    from .native import covers as nc
    return nc.remove_cover(win)


def insert_cover(win, name):
    from .native import covers as nc
    return nc.insert_cover(win, name)


# ---------------------------------------------------------------- headers / footers
HEADERS = ["Blank", "Blank (Three Columns)", "Austin", "Banded", "Facet", "Grid", "Integral",
           "Ion", "Retrospect", "Sideline", "Whisp"]
FOOTERS = ["Blank", "Blank (Three Columns)", "Austin", "Banded", "Facet", "Integral", "Ion",
           "Retrospect", "Semaphore", "Sideline"]


def _field(m, kind):
    if kind == "page":
        f = m.createInstance("com.sun.star.text.textfield.PageNumber")
        f.NumberingType = 4
        f.SubType = values.enum("com.sun.star.text.PageNumberType", "CURRENT")
    elif kind == "pages":
        f = m.createInstance("com.sun.star.text.textfield.PageCount")
        f.NumberingType = 4
    elif kind == "title":
        f = m.createInstance("com.sun.star.text.textfield.docinfo.Title")
    elif kind == "author":
        f = m.createInstance("com.sun.star.text.textfield.docinfo.CreateAuthor")
    elif kind == "date":
        f = m.createInstance("com.sun.star.text.textfield.DateTime")
        f.IsDate = True
        f.IsFixed = False
    else:
        return None
    return f


def hf_design(win, which, name):
    """Put a built-in design in the header or footer of the current
    section."""
    from .native import covers as nc
    return nc.hf_design(win, which, name)


# ---------------------------------------------------------------- galleries
def gallery_parts(gallery):
    from .insertextras import load_parts
    return [p for p in load_parts() if p.get("gallery") == gallery]


def insert_saved(win, part, where):
    """A design saved by the user: a cover page goes at the start, header
    and footer content into the header / footer."""
    return


def save_selection(win, gallery):
    from . import insertextras
    insertextras.save_selection_as_part(win, gallery)
