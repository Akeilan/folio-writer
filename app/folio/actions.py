"""App actions: everything a key, button or menu can do."""
import json
import re

from gi.repository import Gdk, GLib, Gtk

SIZE_STEPS = [8, 9, 10, 10.5, 11, 12, 14, 16, 18, 20, 22, 24, 26, 28, 36, 48, 72]
MM100_PER_INCH = 2540
HALF_INCH = 1270

# Style names: the names shown to the user <-> the engine's names.
TO_ENGINE = {"Normal": "Standard", "Quote": "Quotations", "Body Text": "Text body",
             "TOC Heading": "Contents Heading", "Strong": "Strong Emphasis",
             "Hyperlink": "Internet link", "Footnote Text": "Footnote",
             "Endnote Text": "Endnote", "Caption": "Caption",
             "Table of Figures": "Illustration Index 1"}
FROM_ENGINE = {"Default Paragraph Style": "Normal", "Standard": "Normal",
               "Text body": "Body Text", "Body Text": "Body Text", "Quotations": "Quote",
               "Block Quotation": "Quote", "Contents Heading": "TOC Heading",
               "Strong Emphasis": "Strong", "Internet link": "Hyperlink",
               "Internet Link": "Hyperlink", "Footnote": "Footnote Text",
               "Endnote": "Endnote Text", "Preformatted Text": "HTML Preformatted",
               "No Character Style": "Default Paragraph Font",
               "Illustration Index 1": "Table of Figures", "Figure Index 1": "Table of Figures"}
for i in range(1, 10):
    FROM_ENGINE["Contents %d" % i] = "TOC %d" % i
    TO_ENGINE["TOC %d" % i] = "Contents %d" % i
CHAR_STYLES = {"Subtle Emphasis", "Emphasis", "Intense Emphasis", "Strong",
               "Subtle Reference", "Intense Reference", "Book Title", "Hyperlink"}

HIGHLIGHTS = [("Yellow", 0xFFFF00), ("Bright Green", 0x00FF00), ("Turquoise", 0x00FFFF),
              ("Pink", 0xFF00FF), ("Blue", 0x0000FF), ("Red", 0xFF0000),
              ("Dark Blue", 0x000080), ("Teal", 0x008080), ("Green", 0x008000),
              ("Violet", 0x800080), ("Dark Red", 0x800000), ("Dark Yellow", 0x808000),
              ("Gray 50%", 0x808080), ("Gray 25%", 0xC0C0C0), ("Black", 0x000000)]


def _utf8(raw):
    """Clipboard HTML as UTF-8 (browsers may hand it over as UTF-16)."""
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return raw.decode("utf-16").encode("utf-8")
    if len(raw) > 4 and raw[1:2] == b"\x00" and raw[3:4] == b"\x00":
        return raw.decode("utf-16-le", "replace").encode("utf-8")
    return raw


def word_style(engine_name):
    return FROM_ENGINE.get(engine_name, engine_name)


def engine_style(word_name):
    return TO_ENGINE.get(word_name, word_name)


def _float(s, default=0.0):
    try:
        return float(str(s).replace(",", "."))
    except ValueError:
        return default


def para_margins(engine):
    """Current paragraph indents in 1/100 mm: (left, right, first)."""
    ed = getattr(engine, "ed", None)
    if ed is not None:
        v = ed.para_values()
        k = 2540.0 / 1440.0
        return (int(round(v.get("ind_left", 0) * k)), int(round(v.get("ind_right", 0) * k)),
                int(round(v.get("ind_first", 0) * k)))
    raw = engine.get(".uno:LeftRightParaMargin")
    try:
        d = json.loads(raw)
    except ValueError:
        return 0, 0, 0
    f = MM100_PER_INCH if d.get("unit", "inch") == "inch" else 1000
    return (int(round(_float(d.get("left")) * f)), int(round(_float(d.get("right")) * f)),
            int(round(_float(d.get("firstline")) * f)))


def para_spacing(engine):
    return _para_spacing_state(engine)


def _para_spacing_state(engine):
    raw = engine.get(".uno:ULSpacing")
    try:
        d = json.loads(raw)
    except ValueError:
        return 0, 0
    f = MM100_PER_INCH if d.get("unit", "inch") == "inch" else 1000
    return int(round(_float(d.get("upper")) * f)), int(round(_float(d.get("lower")) * f))


class Actions:
    def __init__(self, window):
        self.win = window
        self.format_copy = None

    @property
    def eng(self):
        return self.win.engine

    # ------------------------------------------------------------ editing
    def insert_text(self, text):
        self.cmd(".uno:InsertText", {"Text": text})

    # Undo/redo run in "repair" mode so changes the app made through the
    # document model (equations, page setup, captions...) undo like typing.
    REPAIR = {"Repair": ("boolean", "true")}

    def do_nbsp(self):
        self.insert_text(" ")

    def do_soft_hyphen(self):
        self.insert_text("­")

    def do_nb_hyphen(self):
        self.insert_text("‑")

    # clipboard: keep the desktop clipboard in sync with the document
    def _clipboard(self):
        return Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)

    def default_paste_mode(self):
        st = self.win.app.settings
        key = "paste_within" if self.win.clipboard_owned else "paste_other"
        return st.get(key, "source")

    def _clipboard_html(self):
        if self.win.clipboard_owned and getattr(self, "_clip_data", None):
            return self._clip_data[0]
        sel = self._clipboard().wait_for_contents(Gdk.Atom.intern("text/html", False))
        if sel is not None and sel.get_length() > 0:
            return _utf8(bytes(sel.get_data())).decode("utf-8", "replace")
        return None

    def _paste(self, mode="source"):
        """Paste as Keep Source Formatting ("source"), Merge Formatting
        ("merge") or Keep Text Only ("text")."""
        if mode is True:
            mode = "text"
        elif mode is False:
            mode = "source"
        if mode == "merge":
            html_src = self._clipboard_html()
            if html_src:
                from .pasteopts import merge_html
                self.eng.paste_data("text/html", merge_html(html_src).encode("utf-8"))
                return
            mode = "text"
        self.eng.paste(plain=mode == "text")

    # format painter (Ctrl+Shift+C / Ctrl+Shift+V)
    CHAR_PROPS = ("CharStyleName", "CharFontName", "CharFontNameAsian", "CharFontNameComplex",
                  "CharHeight", "CharWeight", "CharPosture", "CharUnderline",
                  "CharUnderlineColor", "CharUnderlineHasColor", "CharStrikeout", "CharColor",
                  "CharBackColor", "CharHighlight", "CharEscapement",
                  "CharEscapementHeight", "CharCaseMap", "CharKerning", "CharScaleWidth",
                  "CharShadowed", "CharContoured", "CharRelief", "CharHidden", "CharLocale",
                  "CharTransparence")
    PARA_PROPS = ("ParaAdjust", "ParaLastLineAdjust", "ParaLeftMargin", "ParaRightMargin",
                  "ParaFirstLineIndent", "ParaTopMargin", "ParaBottomMargin",
                  "ParaLineSpacing", "ParaContextMargin", "ParaBackColor", "ParaTabStops",
                  "TopBorder", "BottomBorder", "LeftBorder", "RightBorder",
                  "TopBorderDistance", "BottomBorderDistance", "LeftBorderDistance",
                  "RightBorderDistance", "ParaKeepTogether", "ParaSplit", "ParaWidows",
                  "ParaOrphans", "OutlineLevel")

    def do_format_painter(self):
        self.cmd(".uno:FormatPaintbrush")

    # ------------------------------------------------------------ characters
    def font_name(self, name):
        self.cmd(".uno:CharFontName", {"CharFontName.FamilyName": name})

    def font_size(self, size):
        try:
            v = float(str(size).replace(",", "."))
        except ValueError:
            return
        v = max(1.0, min(1638.0, v))
        self.cmd(".uno:FontHeight", {"FontHeight.Height": ("float", repr(v))})

    def _cur_size(self):
        return _float(self.eng.get(".uno:FontHeight"), 11.0) or 11.0

    def do_grow_font(self):
        s = self._cur_size()
        nxt = next((x for x in SIZE_STEPS if x > s + 0.01), (int(s) // 10 + 1) * 10)
        self.font_size(nxt)

    def do_shrink_font(self):
        s = self._cur_size()
        prv = next((x for x in reversed(SIZE_STEPS) if x < s - 0.01), max(1, s - 1))
        self.font_size(prv)

    def do_grow_font_1(self):
        self.font_size(self._cur_size() + 1)

    def do_shrink_font_1(self):
        self.font_size(max(1, self._cur_size() - 1))

    def do_double_underline(self):
        self.cmd(".uno:UnderlineDouble")

    CASE_CYCLE = [".uno:ChangeCaseToLower", ".uno:ChangeCaseToUpper",
                  ".uno:ChangeCaseToTitleCase"]

    def font_color(self, color):
        self.cmd(".uno:Color", {"Color": ("long", color)})

    def highlight(self, color):
        self.cmd(".uno:CharBackColor", {"CharBackColor.Color": ("long", color)})

    def do_highlight(self):
        self.highlight(getattr(self.win, "last_highlight", 0xFFFF00))

    def do_font_color(self):
        self.font_color(getattr(self.win, "last_font_color", 0xC00000))

    def do_spacing_1(self):
        self.line_spacing(1.0)

    def do_spacing_15(self):
        self.line_spacing(1.5)

    def do_spacing_2(self):
        self.line_spacing(2.0)

    def do_promote(self):
        self.eng.sync(lambda: self._heading_step(-1))

    def do_demote(self):
        self.eng.sync(lambda: self._heading_step(1))

    # ------------------------------------------------------------ view
    def do_zoom_in(self):
        self.win.status.step_zoom(10)

    def do_zoom_out(self):
        self.win.status.step_zoom(-10)
