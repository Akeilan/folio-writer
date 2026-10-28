"""OpenDocument text (.odt, .ott, .fodt) read by Folio itself into the shared
document model (docxbuild.Doc), which is then opened as a Word document."""
import base64
import os
import re
import zipfile
import xml.etree.ElementTree as ET

from . import docxbuild as B

NS = {
    "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
    "style": "urn:oasis:names:tc:opendocument:xmlns:style:1.0",
    "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
    "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
    "draw": "urn:oasis:names:tc:opendocument:xmlns:drawing:1.0",
    "fo": "urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0",
    "xlink": "http://www.w3.org/1999/xlink",
    "dc": "http://purl.org/dc/elements/1.1/",
    "meta": "urn:oasis:names:tc:opendocument:xmlns:meta:1.0",
    "svg": "urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0",
    "loext": "urn:org:documentfoundation:names:experimental:office:xmlns:loext:1.0",
}


def q(tag):
    p, _, n = tag.partition(":")
    return "{%s}%s" % (NS[p], n)


def A(el, name, default=None):
    return el.get(q(name), default)


# --------------------------------------------------------------------- units
_UNIT = {"cm": 566.929, "mm": 56.6929, "in": 1440.0, "inch": 1440.0, "pt": 20.0, "pc": 240.0,
         "px": 15.0}


def twips(v, default=None):
    """'1.25cm' -> twips."""
    if v is None:
        return default
    m = re.match(r"\s*(-?[0-9.]+)\s*([a-z]*)", v)
    if not m:
        return default
    try:
        n = float(m.group(1))
    except ValueError:
        return default
    return int(round(n * _UNIT.get(m.group(2) or "pt", 20.0)))


def colour(v):
    if not v or v == "transparent" or not v.startswith("#"):
        return None
    v = v[1:]
    if len(v) == 3:
        v = "".join(c * 2 for c in v)
    return v.upper()[:6]


def border(v):
    """'0.5pt solid #000000' -> (size in eighths, colour, kind, space)."""
    if not v or v == "none":
        return None
    parts = v.split()
    w = 4
    kind = "single"
    col = "000000"
    for p in parts:
        if p[0].isdigit() or p[0] == ".":
            w = max(2, int(round(twips(p, 10) / 20.0 * 8)))
        elif p.startswith("#"):
            col = colour(p) or col
        elif p in ("double",):
            kind = "double"
        elif p in ("dotted",):
            kind = "dotted"
        elif p in ("dashed",):
            kind = "dashed"
        elif p == "none" or p == "hidden":
            return None
    return (w, col, kind, 0)


def decode_name(n):
    """LibreOffice's style names: '_20_' is a space, '_5f_' an underscore..."""
    return re.sub(r"_([0-9a-fA-F]{1,4})_", lambda m: chr(int(m.group(1), 16)), n or "")


# LibreOffice style names that are Word's own styles
WORD_NAME = {"Standard": "Normal", "Default Paragraph Style": "Normal", "Text body": "Body Text",
             "Body Text": "Body Text", "Quotations": "Quote", "Footnote": "Footnote Text",
             "Endnote": "Endnote Text", "Header": "Header", "Footer": "Footer", "Caption": "Caption",
             "Title": "Title", "Subtitle": "Subtitle", "List Paragraph": "List Paragraph",
             "Contents Heading": "TOC Heading", "Preformatted Text": "Plain Text",
             "Internet link": "Hyperlink", "Internet Link": "Hyperlink", "Strong Emphasis": "Strong",
             "Emphasis": "Emphasis", "Signature": "Signature", "Comment": "Comment Text",
             "Illustration": "Caption", "Figure": "Caption", "Table": "Caption", "Drawing": "Caption"}
for _n in range(1, 11):
    WORD_NAME["Heading %d" % _n] = "Heading %d" % min(_n, 9)
    WORD_NAME["Contents %d" % _n] = "TOC %d" % min(_n, 9)
SKIP_CHAR = {"Footnote anchor", "Footnote Symbol", "Footnote Characters", "Endnote anchor",
             "Endnote Symbol", "Endnote Characters", "Numbering Symbols", "Bullet Symbols",
             "Footnote_20_anchor", "Footnote_20_Symbol"}


def text_props(el):
    """style:text-properties -> run properties (font sizes may be percentages: '%' key)."""
    r = {}
    if el is None:
        return r
    fw = A(el, "fo:font-weight")
    if fw:
        r["b"] = fw == "bold" or (fw.isdigit() and int(fw) >= 600)
    fs = A(el, "fo:font-style")
    if fs:
        r["i"] = fs in ("italic", "oblique")
    us = A(el, "style:text-underline-style")
    if us:
        if us == "none":
            r["u"] = "none"
        else:
            typ = A(el, "style:text-underline-type", "single")
            wid = A(el, "style:text-underline-width", "auto")
            u = {"solid": "single", "dotted": "dotted", "dash": "dash", "long-dash": "dashLong",
                 "dot-dash": "dotDash", "dot-dot-dash": "dotDotDash", "wave": "wave"}.get(us, "single")
            if typ == "double":
                u = "wavyDouble" if u == "wave" else "double"
            elif wid == "bold" and u == "single":
                u = "thick"
            if A(el, "style:text-underline-mode") == "skip-white-space" and u == "single":
                u = "words"
            r["u"] = u
    ls = A(el, "style:text-line-through-style")
    if ls:
        if ls == "none":
            r["strike"] = False
        elif A(el, "style:text-line-through-type") == "double":
            r["dstrike"] = True
        else:
            r["strike"] = True
    sz = A(el, "fo:font-size")
    if sz:
        if sz.endswith("%"):
            try:
                r["%"] = float(sz[:-1]) / 100.0
            except ValueError:
                pass
        else:
            t = twips(sz)
            if t:
                r["sz"] = max(2, int(round(t / 10.0)))
    fn = A(el, "style:font-name") or A(el, "fo:font-family")
    if fn:
        r["font"] = fn.strip("'\"")
    fa = A(el, "style:font-name-asian") or A(el, "style:font-family-asian")
    if fa:
        r["font_ea"] = fa.strip("'\"")
    fc = A(el, "style:font-name-complex") or A(el, "style:font-family-complex")
    if fc:
        r["font_cs"] = fc.strip("'\"")
    c = A(el, "fo:color")
    if c and colour(c):
        r["color"] = colour(c)
    if A(el, "style:use-window-font-color") == "true" and "color" not in r:
        r["color"] = "auto"
    bg = A(el, "fo:background-color")
    if bg and colour(bg):
        r["shd"] = colour(bg)
    tp = A(el, "style:text-position")
    if tp:
        first = tp.split()[0]
        if first == "super" or (first.endswith("%") and _num(first[:-1]) > 0):
            r["vert"] = "superscript"
        elif first == "sub" or (first.endswith("%") and _num(first[:-1]) < 0):
            r["vert"] = "subscript"
        elif first == "0%":
            r["vert"] = "baseline"
    fv = A(el, "fo:font-variant")
    if fv == "small-caps":
        r["smallcaps"] = True
    elif fv == "normal":
        r["smallcaps"] = False
    tt = A(el, "fo:text-transform")
    if tt == "uppercase":
        r["caps"] = True
    elif tt == "none":
        r["caps"] = False
    if A(el, "style:text-outline") == "true":
        r["outline"] = True
    sh = A(el, "fo:text-shadow")
    if sh and sh != "none":
        r["shadow"] = True
    rel = A(el, "style:font-relief")
    if rel == "embossed":
        r["emboss"] = True
    elif rel == "engraved":
        r["imprint"] = True
    if A(el, "text:display") == "none":
        r["hidden"] = True
    sp = A(el, "fo:letter-spacing")
    if sp and sp != "normal":
        r["spacing"] = twips(sp, 0)
    sc = A(el, "style:text-scale")
    if sc and sc.endswith("%"):
        r["scale"] = int(_num(sc[:-1]) or 100)
    lang = A(el, "fo:language")
    if lang and lang != "zxx" and lang != "none":
        cty = A(el, "fo:country")
        r["lang"] = lang + ("-" + cty if cty and cty != "none" else "")
    return r


def _num(s):
    try:
        return float(s)
    except ValueError:
        return 0


def para_props(el, tabs_relative=True):
    p = {}
    if el is None:
        return p
    al = A(el, "fo:text-align")
    if al:
        p["align"] = {"start": "left", "left": "left", "center": "center", "end": "right",
                      "right": "right", "justify": "both"}.get(al, "left")
        if al == "justify" and A(el, "fo:text-align-last") == "justify":
            p["align"] = "distribute"
    for k, key in (("fo:margin-top", "sb"), ("fo:margin-bottom", "sa"), ("fo:margin-left", "ind_l"),
                   ("fo:margin-right", "ind_r"), ("fo:text-indent", "ind_first")):
        v = A(el, k)
        if v is not None and not v.endswith("%"):
            p[key] = twips(v, 0)
    if A(el, "style:contextual-spacing") == "true":
        p["contextual"] = True
    lh = A(el, "fo:line-height")
    if lh and lh != "normal":
        if lh.endswith("%"):
            p["line"] = int(round(240 * _num(lh[:-1]) / 100.0))
            p["line_rule"] = "auto"
        else:
            p["line"] = twips(lh, 240)
            p["line_rule"] = "exact"
    elif lh == "normal":
        p["line"] = 240
        p["line_rule"] = "auto"
    la = A(el, "style:line-height-at-least")
    if la:
        p["line"] = twips(la, 240)
        p["line_rule"] = "atLeast"
    ls = A(el, "style:line-spacing")
    if ls and "line" not in p:
        extra = twips(ls, 0)
        if extra:
            p["line"] = 240 + int(extra * 0.83)
            p["line_rule"] = "auto"
    if A(el, "fo:break-before") == "page":
        p["pbb"] = True
    if A(el, "fo:break-after") == "page":
        p["break_after"] = True
    if A(el, "fo:keep-with-next") == "always":
        p["keep_next"] = True
    if A(el, "fo:keep-together") == "always":
        p["keep_lines"] = True
    wd = A(el, "fo:widows")
    if wd is not None:
        p["widow"] = wd != "0"
    bg = A(el, "fo:background-color")
    if bg and colour(bg):
        p["shd"] = colour(bg)
    b = {}
    allb = border(A(el, "fo:border"))
    for side in ("top", "left", "bottom", "right"):
        v = border(A(el, "fo:border-" + side)) or allb
        if v:
            pad = twips(A(el, "fo:padding-" + side) or A(el, "fo:padding"), 0) or 0
            b[side] = (v[0], v[1], v[2], max(0, min(31, pad // 20)))
    if b:
        p["borders"] = b
    if A(el, "style:writing-mode") in ("rl-tb", "rl"):
        p["bidi"] = True
    pn = A(el, "style:page-number")
    if pn and pn.isdigit():
        p["page_start"] = int(pn)
    ts = el.find(q("style:tab-stops"))
    if ts is not None:
        tabs = []
        for t in ts.findall(q("style:tab-stop")):
            pos = twips(A(t, "style:position"), 0)
            kind = {"left": "left", "center": "center", "right": "right", "char": "decimal"}.get(
                A(t, "style:type", "left"), "left")
            lt = A(t, "style:leader-text")
            lead = {".": "dot", "-": "hyphen", "_": "underscore", "·": "middleDot"}.get(lt) if lt else None
            if not lead and A(t, "style:leader-style") in ("dotted",):
                lead = "dot"
            tabs.append((pos, kind, lead))
        p["tabs"] = tabs
        p["_tabs_rel"] = tabs_relative
    return p


LIST_FMT = {"1": "decimal", "a": "lowerLetter", "A": "upperLetter", "i": "lowerRoman",
            "I": "upperRoman", "": "none", "١, ٢, ٣, ...": "arabicAbjad"}


class Reader:
    def __init__(self, path):
        self.path = path
        self.zip = None
        if zipfile.is_zipfile(path):
            self.zip = zipfile.ZipFile(path)
            content = ET.fromstring(self.zip.read("content.xml"))
            try:
                styles = ET.fromstring(self.zip.read("styles.xml"))
            except KeyError:
                styles = None
            try:
                meta = ET.fromstring(self.zip.read("meta.xml"))
            except KeyError:
                meta = None
            try:
                settings = ET.fromstring(self.zip.read("settings.xml"))
            except KeyError:
                settings = None
        else:
            # flat XML (.fodt): everything in one file
            content = ET.parse(path).getroot()
            styles = meta = content
            settings = content
        self.content = content
        self.styles_root = styles
        self.meta_root = meta
        self.settings_root = settings
        self.doc = B.Doc()
        self.fonts = {}
        self.named = {}       # name -> style element (common styles)
        self.auto = {}        # name -> style element (automatic styles: content.xml)
        self.auto_styles = {}  # automatic styles of styles.xml (headers, page layouts)
        self.list_styles = {}  # name -> element
        self.page_layouts = {}
        self.masters = {}
        self.list_index = {}  # list style name -> abstract index
        self.comment_ids = {}
        self.tabs_relative = True
        self.extra_after = []
        self.in_master = False

    # ------------------------------------------------------------ style tables
    def collect(self):
        def fonts(root):
            if root is None:
                return
            for decl in root.iter(q("office:font-face-decls")):
                for f in decl.findall(q("style:font-face")):
                    fam = A(f, "svg:font-family") or A(f, "style:name")
                    self.fonts[A(f, "style:name")] = fam.strip("'\"")
        fonts(self.styles_root)
        fonts(self.content)
        for root, store in ((self.styles_root, None), (self.content, None)):
            if root is None:
                continue
            for sec in list(root.iter(q("office:styles"))):
                for el in sec:
                    if el.tag == q("style:style"):
                        self.named[(A(el, "style:family"), A(el, "style:name"))] = el
                    elif el.tag == q("text:list-style"):
                        self.list_styles[A(el, "style:name")] = el
                    elif el.tag == q("style:default-style"):
                        if A(el, "style:family") == "paragraph":
                            self.default_style = el
            for sec in list(root.iter(q("office:automatic-styles"))):
                target = self.auto if root is self.content else self.auto_styles
                for el in sec:
                    if el.tag == q("style:style"):
                        target[(A(el, "style:family"), A(el, "style:name"))] = el
                    elif el.tag == q("text:list-style"):
                        self.list_styles.setdefault(A(el, "style:name"), el)
                    elif el.tag == q("style:page-layout"):
                        self.page_layouts[A(el, "style:name")] = el
            for sec in list(root.iter(q("office:master-styles"))):
                for el in sec.findall(q("style:master-page")):
                    self.masters[A(el, "style:name")] = el
        if self.settings_root is not None:
            for it in self.settings_root.iter("{urn:oasis:names:tc:opendocument:xmlns:config:1.0}config-item"):
                if it.get("{urn:oasis:names:tc:opendocument:xmlns:config:1.0}name") == "TabsRelativeToIndent":
                    self.tabs_relative = (it.text or "").strip() == "true"

    def font(self, r):
        for k in ("font", "font_ea", "font_cs"):
            if k in r:
                r[k] = self.fonts.get(r[k], r[k])
        return r

    def autos(self):
        """Automatic styles in scope: styles.xml's own while reading master pages."""
        return (self.auto_styles, self.auto) if self.in_master else (self.auto, self.auto_styles)

    def auto_get(self, key):
        a, b = self.autos()
        return a.get(key) if key in a else b.get(key)

    def style_el(self, family, name):
        return self.auto_get((family, name)) or self.named.get((family, name))

    def resolve_size(self, family, name, depth=0):
        """The font size a style ends up with (half points)."""
        el = self.style_el(family, name) if name else None
        if el is None or depth > 20:
            d = getattr(self, "default_style", None)
            r = text_props(d.find(q("style:text-properties"))) if d is not None else {}
            return r.get("sz", 24)
        r = text_props(el.find(q("style:text-properties")))
        if "sz" in r:
            return r["sz"]
        parent = A(el, "style:parent-style-name")
        base = self.resolve_size(family, parent, depth + 1)
        if "%" in r:
            return int(round(base * r["%"]))
        return base

    def tprops(self, el, family, parent_name=None):
        r = self.font(text_props(el.find(q("style:text-properties")) if el is not None else None))
        if "%" in r:
            base = self.resolve_size(family, parent_name)
            r["sz"] = int(round(base * r.pop("%")))
        return r

    def word_style_name(self, name):
        disp = decode_name(name)
        el = self.named.get(("paragraph", name)) or self.named.get(("text", name))
        if el is not None and A(el, "style:display-name"):
            disp = A(el, "style:display-name")
        return WORD_NAME.get(disp, disp)

    def sid(self, name):
        return B.style_id(self.word_style_name(name))

    def build_styles(self):
        d = self.doc
        ds = getattr(self, "default_style", None)
        if ds is not None:
            d.defaults["rpr"] = self.font(text_props(ds.find(q("style:text-properties"))))
            d.defaults["rpr"].pop("%", None)
            d.defaults["rpr"].pop("color", None) if d.defaults["rpr"].get("color") == "auto" else None
            pp = ds.find(q("style:paragraph-properties"))
            if pp is not None:
                td = A(pp, "style:tab-stop-distance")
                if td:
                    d.tab_stop = twips(td, 720) or 720
                d.defaults["ppr"] = {k: v for k, v in para_props(pp).items()
                                     if k in ("widow", "line", "line_rule", "bidi")}
        d.defaults["rpr"].setdefault("sz", 24)
        d.defaults["rpr"].setdefault("font", "Liberation Serif")
        for (family, name), el in self.named.items():
            if family not in ("paragraph", "text"):
                continue
            disp = self.word_style_name(name)
            if family == "text" and (disp in SKIP_CHAR or name in SKIP_CHAR):
                continue
            sid = B.style_id(disp)
            parent = A(el, "style:parent-style-name")
            nxt = A(el, "style:next-style-name")
            ppr = para_props(el.find(q("style:paragraph-properties")), self.tabs_relative) if family == "paragraph" else {}
            ppr.pop("break_after", None)
            rpr = self.tprops(el, family, parent)
            if rpr.get("color") == "auto":
                rpr.pop("color")
            lvl = A(el, "style:default-outline-level")
            if lvl and lvl.isdigit() and family == "paragraph":
                ppr["outline"] = min(8, int(lvl) - 1)
            kind = "paragraph" if family == "paragraph" else "character"
            s = d.add_style(sid, disp, kind, based=self.sid(parent) if parent else (
                None if sid == "Normal" else ("Normal" if kind == "paragraph" else "DefaultParagraphFont")),
                nxt=self.sid(nxt) if nxt else None, ppr=ppr, rpr=rpr, default=sid == "Normal")
            s["custom"] = sid not in B.BUILTIN.values()
            s["_list"] = A(el, "style:list-style-name")
        if not d.style("Normal"):
            d.add_style("Normal", "Normal", "paragraph", default=True)

    def list_for(self, name):
        if name in self.list_index:
            return self.list_index[name]
        el = self.list_styles.get(name)
        if el is None:
            return None
        levels = []
        for lv in range(1, 10):
            found = None
            for ch in el:
                if A(ch, "text:level") == str(lv):
                    found = ch
                    break
            levels.append(self.level(found, lv))
        self.doc.lists.append(levels)
        idx = len(self.doc.lists) - 1
        self.list_index[name] = idx
        return idx

    def level(self, el, lv):
        out = {"ind": 720 * lv, "hang": 360, "fmt": "bullet" if el is None else "decimal"}
        if el is None:
            out["text"] = "•"
            out["font"] = "Symbol"
            return out
        lp = el.find(q("style:list-level-properties"))
        if lp is not None:
            la = lp.find(q("style:list-level-label-alignment"))
            if la is not None:
                ml = twips(A(la, "fo:margin-left"), None)
                ti = twips(A(la, "fo:text-indent"), None)
                if ml is not None:
                    out["ind"] = ml
                if ti is not None:
                    out["hang"] = -ti if ti < 0 else 0
            else:
                sb = twips(A(lp, "text:space-before"), 0) or 0
                mw = twips(A(lp, "text:min-label-width"), 0) or 0
                out["ind"] = sb + mw
                out["hang"] = mw
        if el.tag == q("text:list-level-style-bullet"):
            out["fmt"] = "bullet"
            ch = A(el, "text:bullet-char") or "•"
            out["text"] = ch
            st = A(el, "text:style-name")
            tp = el.find(q("style:text-properties"))
            f = None
            if tp is not None:
                f = A(tp, "style:font-name") or A(tp, "fo:font-family")
            if f:
                out["font"] = self.fonts.get(f, f).strip("'\"")
            elif st is None and ch in "•◦▪–":
                out["font"] = None
            return out
        if el.tag == q("text:list-level-style-image"):
            out["fmt"] = "bullet"
            out["text"] = "•"
            return out
        fmt = LIST_FMT.get(A(el, "style:num-format", "1"), "decimal")
        out["fmt"] = fmt
        start = A(el, "text:start-value")
        out["start"] = int(start) if start and start.isdigit() else 1
        disp = int(A(el, "text:display-levels", "1") or 1)
        pre = A(el, "style:num-prefix", "") or ""
        suf = A(el, "style:num-suffix", "") or ""
        nums = ".".join("%%%d" % i for i in range(max(1, lv - disp + 1), lv + 1))
        out["text"] = pre + (nums if fmt != "none" else "") + suf
        return out

    # ------------------------------------------------------------ page setup
    def section_from_master(self, mname):
        was = self.in_master
        self.in_master = True
        try:
            return self._section_from_master(mname)
        finally:
            self.in_master = was

    def _section_from_master(self, mname):
        s = B.section()
        m = self.masters.get(mname) if mname else None
        if m is None and self.masters:
            m = self.masters.get("Standard") or self.masters.get("Default") or next(iter(self.masters.values()))
        if m is None:
            return s
        s["_master"] = A(m, "style:name")
        pl = self.page_layouts.get(A(m, "style:page-layout-name"))
        hdr_h = ftr_h = 0
        if pl is not None:
            pp = pl.find(q("style:page-layout-properties"))
            if pp is not None:
                s["w"] = twips(A(pp, "fo:page-width"), 12240) or 12240
                s["h"] = twips(A(pp, "fo:page-height"), 15840) or 15840
                s["landscape"] = A(pp, "style:print-orientation") == "landscape"
                mg = s["margins"]
                for side in ("top", "bottom", "left", "right"):
                    v = twips(A(pp, "fo:margin-" + side), None)
                    if v is not None:
                        mg[side] = v
                cols = pp.find(q("style:columns"))
                if cols is not None and int(A(cols, "fo:column-count", "1") or 1) > 1:
                    s["cols"] = int(A(cols, "fo:column-count"))
                    s["col_space"] = twips(A(cols, "fo:column-gap"), 720) or 720
            for kind in ("header", "footer"):
                hs = pl.find(q("style:%s-style" % kind))
                if hs is not None:
                    hp = hs.find(q("style:header-footer-properties"))
                    if hp is not None:
                        h = (twips(A(hp, "fo:min-height"), 0) or twips(A(hp, "svg:height"), 0) or 0)
                        gap = twips(A(hp, "fo:margin-bottom" if kind == "header" else "fo:margin-top"), 0) or 0
                        # LibreOffice's header height includes the spacing below it
                        tot = h if h else gap + 240
                        if kind == "header":
                            hdr_h = tot
                        else:
                            ftr_h = tot
        mg = s["margins"]
        hd = m.find(q("style:header"))
        if hd is not None and A(hd, "style:display") != "false":
            mg["header"] = mg["top"]
            mg["top"] = mg["top"] + max(hdr_h, 240)
            s["headers"]["default"] = self.blocks(hd)
            hl = m.find(q("style:header-left"))
            if hl is not None and A(hl, "style:display") != "false" and len(hl):
                s["headers"]["even"] = self.blocks(hl)
            hf = m.find(q("style:header-first")) or m.find(q("loext:header-first"))
            if hf is not None and A(hf, "style:display") != "false":
                s["headers"]["first"] = self.blocks(hf)
                s["title_pg"] = True
        else:
            mg["header"] = max(0, mg["top"] // 2)
        ft = m.find(q("style:footer"))
        if ft is not None and A(ft, "style:display") != "false":
            mg["footer"] = mg["bottom"]
            mg["bottom"] = mg["bottom"] + max(ftr_h, 240)
            s["footers"]["default"] = self.blocks(ft)
            fl = m.find(q("style:footer-left"))
            if fl is not None and A(fl, "style:display") != "false" and len(fl):
                s["footers"]["even"] = self.blocks(fl)
            ff = m.find(q("style:footer-first")) or m.find(q("loext:footer-first"))
            if ff is not None and A(ff, "style:display") != "false":
                s["footers"]["first"] = self.blocks(ff)
                s["title_pg"] = True
        else:
            mg["footer"] = max(0, mg["bottom"] // 2)
        return s

    def master_of(self, el):
        """The master page a paragraph or table starts, if any."""
        name = A(el, "text:style-name") or A(el, "table:style-name")
        fam = "table" if el.tag == q("table:table") else "paragraph"
        seen = 0
        while name and seen < 10:
            st = self.style_el(fam, name)
            if st is None:
                return None
            mp = A(st, "style:master-page-name")
            if mp is not None:
                return mp or None
            name = A(st, "style:parent-style-name") if st is not self.named.get((fam, name)) else None
            seen += 1
        return None

    # ------------------------------------------------------------ content
    def read(self):
        self.collect()
        self.build_styles()
        self.read_meta()
        body = self.content.find(q("office:body"))
        text = body.find(q("office:text")) if body is not None else None
        first = None
        if text is not None:
            for el in text.iter():
                if el.tag in (q("text:p"), q("text:h"), q("table:table")):
                    first = self.master_of(el)
                    break
        sec = self.section_from_master(first)
        self.doc.sections.append(sec)
        self.cur = sec
        if text is not None:
            self.body_blocks(text, sec["blocks"], top=True)
        return self.doc

    def read_meta(self):
        m = self.meta_root
        if m is None:
            return
        for tag, key in (("dc:title", "title"), ("dc:subject", "subject"), ("dc:description", "description"),
                         ("meta:initial-creator", "creator"), ("dc:creator", "last")):
            el = m.find(".//" + q(tag))
            if el is not None and el.text:
                self.doc.meta.setdefault(key, el.text)
        kws = [k.text for k in m.iter(q("meta:keyword")) if k.text]
        if kws:
            self.doc.meta["keywords"] = ", ".join(kws)
        if "creator" not in self.doc.meta and self.doc.meta.get("last"):
            self.doc.meta["creator"] = self.doc.meta["last"]

    def blocks(self, container):
        out = []
        self.body_blocks(container, out)
        return out

    def body_blocks(self, container, out, top=False, list_ctx=None):
        for el in container:
            tag = el.tag
            if top and tag in (q("text:p"), q("text:h"), q("table:table")) and out is self.cur["blocks"]:
                mp = self.master_of(el)
                if mp and self.cur["blocks"] and mp != self.cur.get("_master"):
                    self.new_section(self.section_from_master(mp))
                    out = self.cur["blocks"]
            if tag in (q("text:p"), q("text:h")):
                p = self.paragraph(el, list_ctx)
                out.append(p)
                if p.get("ppr", {}).pop("break_after", None):
                    out.append({"style": None, "ppr": {}, "rpr": {}, "runs": [], "_pbb_next": True})
                if self.extra_after:
                    out.extend(self.extra_after)
                    self.extra_after = []
            elif tag == q("text:list"):
                self.list_blocks(el, out, list_ctx)
            elif tag == q("table:table"):
                out.append(self.table(el))
            elif tag == q("text:section"):
                cols = self.section_cols(el)
                if top and cols and out is self.cur["blocks"]:
                    page_cols = self.cur.get("cols", 1)
                    nxt = dict(self.section_like(self.cur), cols=cols[0], col_space=cols[1], **{"break": "continuous"})
                    if self.cur["blocks"]:
                        self.new_section(nxt)
                    else:
                        self.cur.update(cols=cols[0], col_space=cols[1])
                    self.body_blocks(el, self.cur["blocks"], top=False)
                    self.new_section(dict(self.section_like(self.cur), cols=page_cols, **{"break": "continuous"}))
                    out = self.cur["blocks"]
                else:
                    self.body_blocks(el, out, top=top, list_ctx=list_ctx)
                    if top:
                        out = self.cur["blocks"]
            elif tag in (q("text:table-of-content"), q("text:alphabetical-index"),
                         q("text:illustration-index"), q("text:table-index"), q("text:bibliography"),
                         q("text:user-index"), q("text:object-index")):
                ib = el.find(q("text:index-body"))
                if ib is not None:
                    start = len(out)
                    self.body_blocks(ib, out, list_ctx=list_ctx)
                    if tag == q("text:table-of-content") and len(out) > start:
                        src = el.find(q("text:table-of-content-source"))
                        lv = A(src, "text:outline-level", "3") if src is not None else "3"
                        firstb = None
                        for b in out[start:]:
                            if not b.get("table"):
                                firstb = b
                                break
                        lastb = None
                        for b in reversed(out[start:]):
                            if not b.get("table"):
                                lastb = b
                                break
                        if firstb is not None and lastb is not None:
                            # index title stays out of the field
                            if firstb.get("style") == "TOCHeading" and firstb is not lastb:
                                idx = out.index(firstb, start) + 1
                                firstb = next((b for b in out[idx:] if not b.get("table")), lastb)
                            firstb["runs"] = [{"t": "fbegin", "instr": 'TOC \\o "1-%s" \\h \\z \\u' % lv},
                                              {"t": "fsep"}] + firstb["runs"]
                            lastb["runs"] = lastb["runs"] + [{"t": "fend"}]
            elif tag == q("text:soft-page-break"):
                continue
            elif tag in (q("text:tracked-changes"), q("text:variable-decls"), q("text:sequence-decls"),
                         q("text:user-field-decls"), q("office:forms"), q("text:dde-connection-decls")):
                continue
            elif tag == q("draw:frame") or tag == q("draw:a"):
                p = {"style": None, "ppr": {}, "rpr": {}, "runs": []}
                self.inline(el, p["runs"], {}, None, p)
                out.append(p)
                if self.extra_after:
                    out.extend(self.extra_after)
                    self.extra_after = []
            elif tag in (q("text:list-header"),):
                self.body_blocks(el, out, list_ctx=list_ctx)
        # page breaks after a paragraph become break-before on the next one
        for i, b in enumerate(out):
            if b.get("_pbb_next"):
                b.pop("_pbb_next")
                if i + 1 < len(out) and not out[i + 1].get("table"):
                    out[i + 1].setdefault("ppr", {})["pbb"] = True
                    b["_drop"] = True
                else:
                    b["runs"] = [{"t": "page", "rpr": {}}]
        out[:] = [b for b in out if not b.get("_drop")]

    def section_like(self, s):
        n = {k: v for k, v in s.items() if k not in ("blocks", "headers", "footers")}
        n["margins"] = dict(s["margins"])
        n["headers"] = dict(s["headers"])
        n["footers"] = dict(s["footers"])
        n["blocks"] = []
        return n

    def new_section(self, s):
        s["blocks"] = []
        self.doc.sections.append(s)
        self.cur = s

    def section_cols(self, el):
        st = self.style_el("section", A(el, "text:style-name"))
        if st is None:
            return None
        sp = st.find(q("style:section-properties"))
        if sp is None:
            return None
        c = sp.find(q("style:columns"))
        if c is None:
            return None
        n = int(A(c, "fo:column-count", "1") or 1)
        if n <= 1:
            return None
        return (n, twips(A(c, "fo:column-gap"), 720) or 720)

    def list_blocks(self, el, out, ctx):
        name = A(el, "text:style-name")
        if ctx is None:
            sname = name
            idx = self.list_for(sname) if sname else None
            cont = A(el, "text:continue-numbering") == "true" or A(el, "text:continue-list")
            key = sname
            if idx is None:
                idx = self.list_for_default()
            prev = getattr(self, "_last_num", {}).get(key)
            if cont and prev is not None:
                num = prev
            else:
                self.doc.nums.append((idx, bool(prev is not None)))
                num = len(self.doc.nums) - 1
            self.__dict__.setdefault("_last_num", {})[key] = num
            ctx = {"num": num, "level": 0, "list": idx}
        else:
            ctx = dict(ctx, level=ctx["level"] + 1)
        for item in el:
            if item.tag == q("text:list-item"):
                first = True
                for ch in item:
                    if ch.tag in (q("text:p"), q("text:h")):
                        p = self.paragraph(ch, ctx if first else dict(ctx, header=True))
                        out.append(p)
                        if self.extra_after:
                            out.extend(self.extra_after)
                            self.extra_after = []
                        first = False
                    elif ch.tag == q("text:list"):
                        self.list_blocks(ch, out, ctx)
                        first = False
                    elif ch.tag == q("table:table"):
                        out.append(self.table(ch))
            elif item.tag == q("text:list-header"):
                for ch in item:
                    if ch.tag in (q("text:p"), q("text:h")):
                        out.append(self.paragraph(ch, dict(ctx, header=True)))
                    elif ch.tag == q("text:list"):
                        self.list_blocks(ch, out, ctx)

    def list_for_default(self):
        if not hasattr(self, "_default_list"):
            self.doc.lists.append([{"fmt": "bullet", "text": "•", "ind": 720 * (i + 1), "hang": 360}
                                   for i in range(9)])
            self._default_list = len(self.doc.lists) - 1
        return self._default_list

    def para_style(self, el):
        """(named style id, direct paragraph props, direct run props, list style)"""
        name = A(el, "text:style-name")
        ppr, rpr = {}, {}
        lst = None
        st = self.auto_get(("paragraph", name))
        if st is not None:
            parent = A(st, "style:parent-style-name")
            ppr = para_props(st.find(q("style:paragraph-properties")), self.tabs_relative)
            rpr = self.tprops(st, "paragraph", parent)
            lst = A(st, "style:list-style-name")
            name = parent
        sid = self.sid(name) if name else "Normal"
        if not self.doc.style(sid):
            sid = "Normal"
        if lst is None and self.doc.style(sid):
            lst = self.doc.style(sid).get("_list")
        return sid, ppr, rpr, lst

    def paragraph(self, el, list_ctx=None):
        sid, ppr, rpr, lst = self.para_style(el)
        if el.tag == q("text:h"):
            lvl = A(el, "text:outline-level")
            if lvl and lvl.isdigit() and not sid.startswith("Heading"):
                want = "Heading%d" % min(9, int(lvl))
                if self.doc.style(want):
                    sid = want
                else:
                    ppr["outline"] = min(8, int(lvl) - 1)
        if rpr.get("color") == "auto":
            rpr.pop("color")
        ppr.pop("page_start", None) if not ppr.get("page_start") else None
        if ppr.get("page_start"):
            self.cur["page_start"] = ppr.pop("page_start")
        p = {"style": sid, "ppr": ppr, "rpr": dict(rpr), "runs": []}
        if list_ctx is not None:
            for k in ("ind_l", "ind_first"):
                ppr.pop(k, None)
            if list_ctx.get("header"):
                lv = self.doc.lists[list_ctx["list"]][min(8, list_ctx["level"])]
                ppr["ind_l"] = lv.get("ind", 720)
                ppr["ind_first"] = 0
            else:
                ppr["num"] = (list_ctx["num"], min(8, list_ctx["level"]))
        elif lst and el.tag == q("text:p") and lst in self.list_styles and A(el, "text:style-name"):
            pass
        if ppr.get("tabs") and ppr.pop("_tabs_rel", False):
            base = ppr.get("ind_l")
            if base is None:
                s = self.doc.style(sid)
                base = (s or {}).get("ppr", {}).get("ind_l", 0) if s else 0
            if base:
                ppr["tabs"] = [(pos + base, k, l) for pos, k, l in ppr["tabs"]]
        else:
            ppr.pop("_tabs_rel", None)
        self.ws_space = True
        self.inline(el, p["runs"], rpr, None, p)
        # trailing collapsed space
        if p["runs"] and p["runs"][-1].get("t") == "text" and p["runs"][-1].get("_ws"):
            p["runs"][-1]["text"] = p["runs"][-1]["text"].rstrip(" ")
        return p

    def span_props(self, name):
        st = self.auto_get(("text", name))
        cstyle = None
        if st is not None:
            parent = A(st, "style:parent-style-name")
            r = self.tprops(st, "text", parent)
            if parent:
                cid = self.sid(parent)
                if self.doc.style(cid):
                    cstyle = cid
            return r, cstyle
        if name and self.named.get(("text", name)) is not None:
            cid = self.sid(name)
            if self.doc.style(cid):
                return {}, cid
        return {}, None

    def add_text(self, runs, s, rpr, cstyle, ws=True):
        if not s:
            return
        if ws:
            s = re.sub(r"[ \t\r\n]+", " ", s)
            if s.startswith(" ") and self.ws_space:
                s = s[1:]
            if not s:
                return
            self.ws_space = s.endswith(" ")
        else:
            self.ws_space = False
        if runs and runs[-1]["t"] == "text" and runs[-1]["rpr"] == rpr and runs[-1].get("cstyle") == cstyle:
            runs[-1]["text"] += s
            runs[-1]["_ws"] = ws
        else:
            runs.append({"t": "text", "text": s, "rpr": dict(rpr), "cstyle": cstyle, "_ws": ws})

    def inline(self, el, runs, rpr, cstyle, para):
        self.add_text(runs, el.text, rpr, cstyle)
        for ch in el:
            tag = ch.tag
            if tag == q("text:span"):
                r2, c2 = self.span_props(A(ch, "text:style-name"))
                merged = dict(rpr)
                merged.update(r2)
                if merged.get("color") == "auto":
                    merged.pop("color")
                self.inline(ch, runs, merged, c2 or cstyle, para)
            elif tag == q("text:s"):
                n = int(A(ch, "text:c", "1") or 1)
                self.add_text(runs, " " * n, rpr, cstyle, ws=False)
            elif tag == q("text:tab"):
                self.add_text(runs, "\t", rpr, cstyle, ws=False)
            elif tag == q("text:line-break"):
                self.add_text(runs, "\n", rpr, cstyle, ws=False)
                self.ws_space = True
            elif tag == q("text:a"):
                href = A(ch, "xlink:href", "")
                inner = []
                cs = A(ch, "text:style-name")
                c2 = self.sid(cs) if cs and self.named.get(("text", cs)) is not None else None
                if c2 and not self.doc.style(c2):
                    c2 = None
                self.inline(ch, inner, rpr, c2 or cstyle, para)
                if href.startswith("#"):
                    anchor = href[1:]
                    if "|" in anchor:
                        inner_link = {"t": "link", "anchor": None, "runs": inner}
                    else:
                        inner_link = {"t": "link", "anchor": anchor, "runs": inner}
                    runs.append(inner_link)
                else:
                    if c2 is None and not any(r.get("cstyle") for r in inner):
                        for r in inner:
                            if r["t"] == "text":
                                r["cstyle"] = "Hyperlink" if self.doc.style("Hyperlink") or True else None
                    runs.append({"t": "link", "url": href, "runs": inner})
            elif tag == q("text:note"):
                body = ch.find(q("text:note-body"))
                kind = A(ch, "text:note-class", "footnote")
                blocks = self.blocks(body) if body is not None else []
                for b in blocks:
                    if not b.get("table") and b.get("style") in ("Normal", None):
                        b["style"] = "EndnoteText" if kind == "endnote" else "FootnoteText"
                runs.append({"t": "note", "kind": kind, "blocks": blocks, "rpr": {}})
                self.ws_space = False
            elif tag == q("office:annotation"):
                self.comment(ch, runs)
            elif tag == q("office:annotation-end"):
                cid = self.comment_ids.get(A(ch, "office:name"))
                if cid is not None:
                    runs.append({"t": "cend", "id": cid})
            elif tag == q("text:bookmark"):
                n = A(ch, "text:name")
                runs.append({"t": "bmstart", "name": n})
                runs.append({"t": "bmend", "name": n})
            elif tag == q("text:bookmark-start"):
                runs.append({"t": "bmstart", "name": A(ch, "text:name")})
            elif tag == q("text:bookmark-end"):
                runs.append({"t": "bmend", "name": A(ch, "text:name")})
            elif tag == q("draw:frame"):
                self.frame(ch, runs, rpr, para)
            elif tag == q("draw:a"):
                for fr in ch:
                    if fr.tag == q("draw:frame"):
                        self.frame(fr, runs, rpr, para)
            elif tag in FIELDS:
                instr = FIELDS[tag](ch)
                res = "".join(ch.itertext())
                if instr:
                    runs.append({"t": "field", "instr": instr, "result": res, "rpr": dict(rpr)})
                    self.ws_space = False
                else:
                    self.add_text(runs, res, rpr, cstyle, ws=False)
            elif tag in (q("text:soft-page-break"), q("text:reference-mark-start"),
                         q("text:reference-mark-end"), q("text:reference-mark"), q("text:change"),
                         q("text:change-start"), q("text:change-end"), q("text:alphabetical-index-mark"),
                         q("text:toc-mark"), q("text:toc-mark-start"), q("text:toc-mark-end"),
                         q("text:alphabetical-index-mark-start"), q("text:alphabetical-index-mark-end")):
                pass
            elif tag == q("draw:custom-shape") or tag == q("draw:rect") or tag == q("draw:ellipse") \
                    or tag == q("draw:line") or tag == q("draw:g"):
                # drawn shapes: their text, so nothing is lost
                txt = [b for b in self.blocks(ch) if b.get("runs")]
                self.extra_after.extend(txt)
            else:
                self.inline(ch, runs, rpr, cstyle, para)
            self.add_text(runs, ch.tail, rpr, cstyle)

    def comment(self, el, runs):
        d = self.doc
        cid = len(d.comments)
        author = ""
        date = ""
        initials = ""
        blocks = []
        for ch in el:
            if ch.tag == q("dc:creator"):
                author = ch.text or ""
            elif ch.tag == q("dc:date"):
                date = (ch.text or "")[:19]
                if date and not date.endswith("Z"):
                    date += "Z"
            elif ch.tag == q("meta:creator-initials") or ch.tag.endswith("}sender-initials"):
                initials = ch.text or ""
            elif ch.tag in (q("text:p"), q("text:list"), q("text:h")):
                tmp = []
                self.body_blocks([ch], tmp) if False else None
                if ch.tag == q("text:list"):
                    self.list_blocks(ch, tmp, None)
                else:
                    tmp.append(self.paragraph(ch))
                for b in tmp:
                    b["style"] = "CommentText"
                blocks.extend(tmp)
        d.comments.append({"id": cid, "author": author, "date": date, "initials": initials,
                           "blocks": blocks})
        name = A(el, "office:name")
        runs.append({"t": "cstart", "id": cid})
        if name:
            self.comment_ids[name] = cid
        else:
            runs.append({"t": "cend", "id": cid})

    def frame(self, fr, runs, rpr, para):
        w = twips(A(fr, "svg:width"), 1440) or 1440
        h = twips(A(fr, "svg:height"), 1440) or 1440
        anchor = A(fr, "text:anchor-type", "as-char")
        imgs = fr.findall(q("draw:image"))
        tb = fr.find(q("draw:text-box"))
        if tb is not None:
            blocks = self.blocks(tb)
            self.extra_after.extend(blocks)
            return
        obj = fr.find(q("draw:object")) or fr.find(q("draw:object-ole"))
        pick = None
        for im in imgs:
            href = A(im, "xlink:href", "") or ""
            ext = os.path.splitext(href)[1].lower().lstrip(".")
            data = None
            if href and self.zip is not None:
                try:
                    data = self.zip.read(href.lstrip("./"))
                except KeyError:
                    data = None
            else:
                bd = im.find(q("office:binary-data"))
                if bd is not None and bd.text:
                    data = base64.b64decode(bd.text)
                    ext = _sniff(data)
            if not data:
                continue
            if not ext or ext not in ("png", "jpg", "jpeg", "gif", "bmp", "tif", "tiff", "emf", "wmf", "svg"):
                ext = _sniff(data)
            if ext in ("svg",) and pick is not None:
                continue
            if ext in ("png", "jpg", "jpeg", "gif", "bmp", "tif", "tiff", "emf", "wmf"):
                pick = (data, ext)
                break
            if pick is None and ext:
                pick = (data, ext)
        if pick is None:
            if obj is not None:
                # an embedded object with no picture to show
                return
            return
        data, ext = pick
        if ext == "svg":
            return
        title = fr.find(q("svg:title"))
        desc = fr.find(q("svg:desc"))
        r = {"t": "image", "data": data, "ext": ext, "cx": w * B.EMU_PER_TWIP, "cy": h * B.EMU_PER_TWIP,
             "name": A(fr, "draw:name") or "", "descr": (desc.text if desc is not None else None) or
             (title.text if title is not None else "") or "", "rpr": {}}
        if anchor in ("paragraph", "char", "page"):
            gs = self.merged_graphic(A(fr, "draw:style-name"))
            wrap = "square"
            behind = False
            hrel, vrel = "column", "paragraph"
            halign = valign = None
            if gs is not None:
                gp = gs.find(q("style:graphic-properties"))
                if gp is not None:
                    wr = A(gp, "style:wrap", "parallel")
                    wrap = {"none": "top", "run-through": "none", "parallel": "square",
                            "dynamic": "square", "left": "square", "right": "square"}.get(wr, "square")
                    if wr == "run-through" and A(gp, "style:run-through") == "background":
                        behind = True
                    hrel = {"page": "page", "paragraph": "column", "page-content": "margin"}.get(
                        A(gp, "style:horizontal-rel", ""), "column")
                    vrel = {"page": "page", "paragraph": "paragraph", "page-content": "margin"}.get(
                        A(gp, "style:vertical-rel", ""), "paragraph")
                    hp = A(gp, "style:horizontal-pos", "")
                    if hp in ("left", "right", "center", "inside", "outside"):
                        halign = hp
                    vp = A(gp, "style:vertical-pos", "")
                    if vp in ("top", "middle", "bottom"):
                        valign = {"middle": "center"}.get(vp, vp)
            if anchor == "page":
                hrel = vrel = "page"
            x = twips(A(fr, "svg:x"), 0) or 0
            y = twips(A(fr, "svg:y"), 0) or 0
            r["anchor"] = {"wrap": wrap, "behind": behind, "hrel": hrel, "vrel": vrel,
                           "x": x * B.EMU_PER_TWIP, "y": y * B.EMU_PER_TWIP,
                           "halign": halign, "valign": valign if vrel != "paragraph" else None}
        runs.append(r)
        self.ws_space = False

    def merged_graphic(self, name):
        """A graphic style with what it inherits, as one style:graphic-properties element."""
        chain = []
        seen = 0
        while name and seen < 10:
            st = self.style_el("graphic", name)
            if st is None:
                break
            chain.append(st)
            name = A(st, "style:parent-style-name")
            seen += 1
        if not chain:
            return None
        gp = ET.Element(q("style:graphic-properties"))
        for st in reversed(chain):
            g = st.find(q("style:graphic-properties"))
            if g is not None:
                gp.attrib.update(g.attrib)
        out = ET.Element(q("style:style"))
        out.append(gp)
        return out

    # ------------------------------------------------------------ tables
    def table(self, el):
        ts = self.style_el("table", A(el, "table:style-name"))
        t = {"table": True, "rows": [], "cols": [], "borders": False}
        if ts is not None:
            tp = ts.find(q("style:table-properties"))
            if tp is not None:
                w = twips(A(tp, "style:width"), None)
                if w:
                    t["width"] = w
                al = A(tp, "table:align")
                if al in ("center", "right"):
                    t["align"] = al
                ml = twips(A(tp, "fo:margin-left"), None)
                if ml and al in (None, "left", "margins"):
                    t["indent"] = ml
        cols = []
        for c in el.iter(q("table:table-column")):
            n = int(A(c, "table:number-columns-repeated", "1") or 1)
            cs = self.style_el("table-column", A(c, "table:style-name"))
            w = None
            if cs is not None:
                cp = cs.find(q("style:table-column-properties"))
                if cp is not None:
                    w = twips(A(cp, "style:column-width"), None)
            cols.extend([w] * min(n, 64))
        pending = {}   # grid col -> [rows left, span]

        def rows_of(parent, header=False):
            for r in parent:
                if r.tag == q("table:table-row"):
                    yield r, header
                elif r.tag == q("table:table-header-rows"):
                    yield from rows_of(r, True)
                elif r.tag in (q("table:table-rows"), q("table:table-row-group")):
                    yield from rows_of(r, header)
        for row, header in rows_of(el):
            rs = self.style_el("table-row", A(row, "table:style-name"))
            out = {"cells": [], "header": header}
            if rs is not None:
                rp = rs.find(q("style:table-row-properties"))
                if rp is not None:
                    h = twips(A(rp, "style:row-height"), None)
                    mh = twips(A(rp, "style:min-row-height"), None)
                    if h:
                        out["height"] = h
                        out["exact"] = True
                    elif mh:
                        out["height"] = mh
                    if A(rp, "fo:keep-together") == "always" or A(rp, "style:keep-together") == "false":
                        out["cant_split"] = A(rp, "fo:keep-together") == "always"
            col = 0
            for cell in row:
                if cell.tag not in (q("table:table-cell"), q("table:covered-table-cell")):
                    continue
                rep = int(A(cell, "table:number-columns-repeated", "1") or 1)
                for _ in range(min(rep, 64)):
                    if cell.tag == q("table:covered-table-cell"):
                        if col in pending:
                            left, span = pending[col]
                            out["cells"].append({"vmerge": "cont", "span": span, "blocks": [B.para()]})
                            if left <= 1:
                                del pending[col]
                            else:
                                pending[col] = [left - 1, span]
                        col += 1
                        continue
                    span = int(A(cell, "table:number-columns-spanned", "1") or 1)
                    rspan = int(A(cell, "table:number-rows-spanned", "1") or 1)
                    c = {"span": span, "blocks": self.blocks(cell)}
                    if rspan > 1:
                        c["vmerge"] = "restart"
                        pending[col] = [rspan - 1, span]
                    cst = self.style_el("table-cell", A(cell, "table:style-name"))
                    if cst is not None:
                        cp = cst.find(q("style:table-cell-properties"))
                        if cp is not None:
                            bg = colour(A(cp, "fo:background-color"))
                            if bg:
                                c["shd"] = bg
                            bd = {}
                            allb = border(A(cp, "fo:border"))
                            for side in ("top", "left", "bottom", "right"):
                                v = border(A(cp, "fo:border-" + side)) or (allb if A(cp, "fo:border-" + side) is None else None)
                                if v:
                                    bd[side] = v
                            if bd:
                                c["borders"] = bd
                            va = A(cp, "style:vertical-align")
                            if va in ("middle", "bottom"):
                                c["valign"] = "center" if va == "middle" else "bottom"
                    if not c["blocks"]:
                        c["blocks"] = [B.para()]
                    out["cells"].append(c)
                    col += 1
            t["rows"].append(out)
        ncol = max((sum(c.get("span", 1) for c in r["cells"]) for r in t["rows"]), default=0)
        if cols and None not in cols[:ncol] and len(cols) >= ncol:
            t["cols"] = cols[:ncol] if ncol else cols
        elif ncol:
            total = t.get("width") or (self.cur["w"] - self.cur["margins"]["left"] - self.cur["margins"]["right"])
            t["cols"] = [total // ncol] * ncol
        return t


def _sniff(data):
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if data[:3] == b"\xff\xd8\xff":
        return "jpg"
    if data[:4] in (b"GIF8",):
        return "gif"
    if data[:2] == b"BM":
        return "bmp"
    if data[:4] in (b"II*\x00", b"MM\x00*"):
        return "tif"
    if data[:4] == b"\x01\x00\x00\x00" and data[40:44] == b" EMF":
        return "emf"
    if data[:4] == b"\xd7\xcd\xc6\x9a" or data[:4] == b"\x01\x00\x09\x00":
        return "wmf"
    if b"<svg" in data[:500]:
        return "svg"
    return ""


def _date_fmt(el):
    return None


FIELDS = {
    q("text:page-number"): lambda e: "PAGE",
    q("text:page-count"): lambda e: "NUMPAGES",
    q("text:word-count"): lambda e: "NUMWORDS",
    q("text:character-count"): lambda e: "NUMCHARS",
    q("text:date"): lambda e: None if A(e, "text:fixed") == "true" else 'DATE \\@ "M/d/yyyy"',
    q("text:time"): lambda e: None if A(e, "text:fixed") == "true" else 'TIME \\@ "h:mm am/pm"',
    q("text:title"): lambda e: "TITLE",
    q("text:subject"): lambda e: "SUBJECT",
    q("text:initial-creator"): lambda e: "AUTHOR",
    q("text:author-name"): lambda e: "AUTHOR",
    q("text:file-name"): lambda e: "FILENAME",
    q("text:sequence"): lambda e: "SEQ %s \\* ARABIC" % (A(e, "text:name") or "Figure").replace(" ", "_"),
    q("text:bookmark-ref"): lambda e: "REF %s \\h" % A(e, "text:ref-name") if A(e, "text:ref-name") else None,
    q("text:sequence-ref"): lambda e: None,
    q("text:chapter"): lambda e: None,
    q("text:sender-firstname"): lambda e: None,
    q("text:user-defined"): lambda e: None,
    q("text:variable-get"): lambda e: None,
    q("text:user-field-get"): lambda e: None,
    q("text:placeholder"): lambda e: None,
    q("text:description"): lambda e: "COMMENTS",
    q("text:keywords"): lambda e: "KEYWORDS",
}


def read(path):
    """The Doc for an .odt/.ott/.fodt file."""
    return Reader(path).read()


def to_docx_file(path, out_path):
    data = B.to_docx(read(path))
    with open(out_path, "wb") as fh:
        fh.write(data)
    return out_path
