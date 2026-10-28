"""OpenDocument text written by Folio itself from the shared document model."""
import datetime
import io
import zipfile
from xml.sax.saxutils import escape as _esc

from . import docxbuild as B

NSDECL = ('xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
          'xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0" '
          'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" '
          'xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" '
          'xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0" '
          'xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0" '
          'xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:dc="http://purl.org/dc/elements/1.1/" '
          'xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0" '
          'xmlns:number="urn:oasis:names:tc:opendocument:xmlns:datastyle:1.0" '
          'xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0" '
          'xmlns:loext="urn:org:documentfoundation:names:experimental:office:xmlns:loext:1.0" '
          'office:version="1.3"')
HDR = '<?xml version="1.0" encoding="UTF-8"?>\n'


def esc(s):
    return _esc(str(s), {'"': "&quot;"})


def cm(tw):
    return "%.4fcm" % (tw / 566.929)


def pt(halfpts):
    return "%gpt" % (halfpts / 2.0)


def col(c):
    return "#" + c.lower() if c and c != "auto" else None


def enc(name):
    """A style name as LibreOffice writes it (spaces as _20_)."""
    out = []
    for ch in name:
        if ch.isalnum() or ch in "-.":
            out.append(ch)
        else:
            out.append("_%x_" % ord(ch))
    return "".join(out)


ODF_NAME = {"Normal": "Standard", "BodyText": "Text body", "Quote": "Quotations",
            "FootnoteText": "Footnote", "EndnoteText": "Endnote", "Hyperlink": "Internet link",
            "PlainText": "Preformatted Text", "Strong": "Strong Emphasis", "TOCHeading": "Contents Heading",
            "CommentText": "Comment"}
for _n in range(1, 10):
    ODF_NAME["TOC%d" % _n] = "Contents %d" % _n

HIGHLIGHT = {"yellow": "ffff00", "green": "00ff00", "cyan": "00ffff", "magenta": "ff00ff",
             "blue": "0000ff", "red": "ff0000", "darkBlue": "000080", "darkCyan": "008080",
             "darkGreen": "008000", "darkMagenta": "800080", "darkRed": "800000",
             "darkYellow": "808000", "darkGray": "808080", "lightGray": "c0c0c0", "black": "000000",
             "white": "ffffff"}
NUM_FMT = {"decimal": "1", "lowerLetter": "a", "upperLetter": "A", "lowerRoman": "i",
           "upperRoman": "I", "none": "", "decimalZero": "1", "ordinal": "1", "cardinalText": "1"}


def text_attrs(r, fonts):
    a = []
    if r.get("font"):
        fonts.add(r["font"])
        a.append('style:font-name="%s"' % esc(r["font"]))
    if r.get("font_ea"):
        fonts.add(r["font_ea"])
        a.append('style:font-name-asian="%s"' % esc(r["font_ea"]))
    if r.get("font_cs"):
        fonts.add(r["font_cs"])
        a.append('style:font-name-complex="%s"' % esc(r["font_cs"]))
    if r.get("sz"):
        a.append('fo:font-size="%s" style:font-size-asian="%s" style:font-size-complex="%s"' % ((pt(r["sz"]),) * 3))
    if "b" in r:
        v = "bold" if r["b"] else "normal"
        a.append('fo:font-weight="%s" style:font-weight-asian="%s" style:font-weight-complex="%s"' % (v, v, v))
    if "i" in r:
        v = "italic" if r["i"] else "normal"
        a.append('fo:font-style="%s" style:font-style-asian="%s" style:font-style-complex="%s"' % (v, v, v))
    if "u" in r:
        u = r["u"]
        if not u or u == "none":
            a.append('style:text-underline-style="none"')
        else:
            style = {"dotted": "dotted", "dottedHeavy": "dotted", "dash": "dash", "dashedHeavy": "dash",
                     "dashLong": "long-dash", "dotDash": "dot-dash", "dotDotDash": "dot-dot-dash",
                     "wave": "wave", "wavyDouble": "wave", "wavyHeavy": "wave"}.get(u, "solid")
            extra = ''
            if u in ("double", "wavyDouble"):
                extra = ' style:text-underline-type="double"'
            if u in ("thick", "dottedHeavy", "dashedHeavy", "wavyHeavy"):
                extra += ' style:text-underline-width="bold"'
            if u == "words":
                extra += ' style:text-underline-mode="skip-white-space"'
            a.append('style:text-underline-style="%s" style:text-underline-width="auto" '
                     'style:text-underline-color="font-color"%s' % (style, extra))
    if r.get("dstrike"):
        a.append('style:text-line-through-style="solid" style:text-line-through-type="double"')
    elif "strike" in r:
        a.append('style:text-line-through-style="%s"' % ("solid" if r["strike"] else "none"))
    if r.get("color"):
        c = col(r["color"])
        if c:
            a.append('fo:color="%s"' % c)
    bg = r.get("shd") or HIGHLIGHT.get(r.get("highlight") or "")
    if bg:
        a.append('fo:background-color="#%s"' % bg.lower())
    v = r.get("vert")
    if v == "superscript":
        a.append('style:text-position="super 58%"')
    elif v == "subscript":
        a.append('style:text-position="sub 58%"')
    if r.get("position"):
        a.append('style:text-position="%d%% 100%%"' % max(-100, min(100, int(r["position"] * 100 / max(1, r.get("sz", 24))))))
    if "smallcaps" in r:
        a.append('fo:font-variant="%s"' % ("small-caps" if r["smallcaps"] else "normal"))
    if "caps" in r:
        a.append('fo:text-transform="%s"' % ("uppercase" if r["caps"] else "none"))
    if r.get("outline"):
        a.append('style:text-outline="true"')
    if r.get("shadow"):
        a.append('fo:text-shadow="1pt 1pt"')
    if r.get("emboss"):
        a.append('style:font-relief="embossed"')
    elif r.get("imprint"):
        a.append('style:font-relief="engraved"')
    if r.get("hidden"):
        a.append('text:display="none"')
    if r.get("spacing"):
        a.append('fo:letter-spacing="%s"' % cm(r["spacing"]))
    if r.get("scale") and r["scale"] != 100:
        a.append('style:text-scale="%d%%"' % r["scale"])
    if r.get("lang"):
        lang, _, cty = r["lang"].partition("-")
        a.append('fo:language="%s"%s' % (esc(lang), ' fo:country="%s"' % esc(cty) if cty else ""))
    return " ".join(a)


def para_attrs(p, base_ind=0):
    a = []
    inner = ""
    if p.get("align"):
        a.append('fo:text-align="%s"' % {"left": "start", "center": "center", "right": "end",
                                         "both": "justify", "distribute": "justify"}.get(p["align"], "start"))
    if "sb" in p:
        a.append('fo:margin-top="%s"' % cm(p["sb"]))
    if "sa" in p:
        a.append('fo:margin-bottom="%s"' % cm(p["sa"]))
    if "ind_l" in p:
        a.append('fo:margin-left="%s"' % cm(p["ind_l"]))
    if "ind_r" in p:
        a.append('fo:margin-right="%s"' % cm(p["ind_r"]))
    if "ind_first" in p:
        a.append('fo:text-indent="%s"' % cm(p["ind_first"]))
    if p.get("contextual"):
        a.append('style:contextual-spacing="true"')
    if "line" in p:
        rule = p.get("line_rule", "auto")
        if rule == "auto":
            a.append('fo:line-height="%d%%"' % round(p["line"] * 100 / 240.0))
        elif rule == "exact":
            a.append('fo:line-height="%s"' % cm(p["line"]))
        else:
            a.append('style:line-height-at-least="%s"' % cm(p["line"]))
    if p.get("pbb"):
        a.append('fo:break-before="page"')
    if p.get("keep_next"):
        a.append('fo:keep-with-next="always"')
    if p.get("keep_lines"):
        a.append('fo:keep-together="always"')
    if "widow" in p:
        v = "2" if p["widow"] else "0"
        a.append('fo:widows="%s" fo:orphans="%s"' % (v, v))
    if p.get("shd"):
        a.append('fo:background-color="#%s"' % p["shd"].lower())
    if p.get("borders"):
        for side, (sz, c, kind, space) in p["borders"].items():
            if side not in ("top", "left", "bottom", "right"):
                continue
            a.append('fo:border-%s="%.2fpt %s #%s" fo:padding-%s="%s"' % (
                side, sz / 8.0, "double" if kind == "double" else "solid", (c or "000000").lower(),
                side, cm(space * 20)))
    if p.get("bidi"):
        a.append('style:writing-mode="rl-tb"')
    if p.get("tabs"):
        t = []
        for pos, kind, leader in p["tabs"]:
            if kind == "clear":
                continue
            k = {"left": "left", "start": "left", "center": "center", "right": "right", "end": "right",
                 "decimal": "char"}.get(kind, "left")
            ls = ""
            if leader and leader != "none":
                ls = ' style:leader-style="%s" style:leader-text="%s"' % (
                    "dotted" if leader in ("dot", "middleDot") else "solid",
                    {"dot": ".", "hyphen": "-", "underscore": "_", "middleDot": "·", "heavy": "_"}.get(leader, "."))
            t.append('<style:tab-stop style:position="%s" style:type="%s"%s%s/>' % (
                cm(pos), k, ' style:char="."' if k == "char" else "", ls))
        inner = "<style:tab-stops>%s</style:tab-stops>" % "".join(t)
    return " ".join(a), inner


class Writer:
    def __init__(self, doc):
        self.doc = doc
        self.fonts = set()
        self.auto = {}       # key -> name (content.xml)
        self.auto_xml = []
        self.sauto = {}      # automatic styles in styles.xml (header/footer paragraphs)
        self.sauto_xml = []
        self.pics = {}
        self.pic_n = 0
        self.frame_n = 0
        self.tbl_n = 0
        self.note_n = 0
        self.list_used = {}
        self.in_styles = False
        self.master_for = {}

    # ---------------------------------------------------------- style registries
    def _auto(self, family, body, prefix, parent=None, extra=""):
        store, out = (self.sauto, self.sauto_xml) if self.in_styles else (self.auto, self.auto_xml)
        key = (family, parent, body, extra)
        if key in store:
            return store[key]
        name = "%s%d" % (("M" if self.in_styles else "") + prefix, len(store) + 1)
        store[key] = name
        out.append('<style:style style:name="%s" style:family="%s"%s%s>%s</style:style>' % (
            name, family, ' style:parent-style-name="%s"' % esc(parent) if parent else "", extra, body))
        return name

    def sname(self, sid):
        """The ODF name of a Word style id."""
        s = self.doc.style(sid) if sid else None
        if s and s.get("default") and s["type"] == "paragraph":
            return "Standard"
        disp = ODF_NAME.get(sid) or ODF_NAME.get(B.style_id(s["name"])) if s else ODF_NAME.get(sid)
        disp = disp or (s["name"] if s else sid) or "Standard"
        return enc(disp)

    def para_style(self, p, master=None):
        ppr = {k: v for k, v in (p.get("ppr") or {}).items() if not k.startswith("_") and k != "num"}
        pa, inner = para_attrs(ppr)
        ta = text_attrs(p.get("rpr") or {}, self.fonts) if p.get("rpr") else ""
        parent = self.sname(p.get("style") or "Normal")
        if not pa and not inner and not ta and not master:
            return parent
        body = ""
        if pa or inner:
            body += "<style:paragraph-properties %s>%s</style:paragraph-properties>" % (pa, inner) if inner else \
                "<style:paragraph-properties %s/>" % pa
        if ta:
            body += "<style:text-properties %s/>" % ta
        extra = ' style:master-page-name="%s"' % master if master else ""
        return self._auto("paragraph", body, "P", parent, extra)

    def text_style(self, r, cstyle=None):
        ta = text_attrs(r, self.fonts) if r else ""
        parent = self.sname(cstyle) if cstyle else None
        if not ta:
            return parent
        return self._auto("text", "<style:text-properties %s/>" % ta, "T", parent)

    # ---------------------------------------------------------- content
    def runs(self, runs, out):
        for r in runs:
            t = r.get("t")
            if t == "text":
                if not r["text"]:
                    continue
                body = self.text(r["text"])
                st = self.text_style(r.get("rpr") or {}, r.get("cstyle"))
                if st:
                    out.append('<text:span text:style-name="%s">%s</text:span>' % (st, body))
                else:
                    out.append(body)
            elif t == "tab":
                out.append("<text:tab/>")
            elif t == "br":
                out.append("<text:line-break/>")
            elif t in ("page", "col"):
                out.append("\x00PAGEBREAK\x00")
            elif t == "image":
                out.append(self.image(r))
            elif t == "note":
                self.note_n += 1
                kind = "endnote" if r.get("kind") == "endnote" else "footnote"
                inner = []
                self.blocks(r.get("blocks") or [], inner)
                out.append('<text:note text:id="ftn%d" text:note-class="%s"><text:note-citation>%d</text:note-citation>'
                           '<text:note-body>%s</text:note-body></text:note>' % (self.note_n, kind, self.note_n, "".join(inner)))
            elif t == "field":
                out.append(self.field(r))
            elif t == "link":
                inner = []
                self.runs(r.get("runs") or [], inner)
                href = r.get("url") or ("#" + r["anchor"] if r.get("anchor") else None)
                if href:
                    out.append('<text:a xlink:type="simple" xlink:href="%s">%s</text:a>' % (esc(href), "".join(inner)))
                else:
                    out.extend(inner)
            elif t == "cstart":
                out.append(self.annotation(r["id"]))
            elif t == "cend":
                out.append('<office:annotation-end office:name="__Annotation__%d"/>' % r["id"])
            elif t == "bmstart":
                out.append('<text:bookmark-start text:name="%s"/>' % esc(r["name"]))
            elif t == "bmend":
                out.append('<text:bookmark-end text:name="%s"/>' % esc(r["name"]))

    def text(self, s):
        """Text with ODF's spaces, tabs and line breaks."""
        out = []
        sp = 0
        prev_space = True
        for ch in s:
            if ch == " ":
                if prev_space:
                    sp += 1
                else:
                    out.append(" ")
                    prev_space = True
                continue
            if sp:
                out.append('<text:s text:c="%d"/>' % sp if sp > 1 else "<text:s/>")
                sp = 0
            prev_space = False
            if ch == "\t":
                out.append("<text:tab/>")
            elif ch in "\n\x0b":
                out.append("<text:line-break/>")
                prev_space = True
            else:
                out.append(esc(B._clean(ch)))
        if sp:
            out.append('<text:s text:c="%d"/>' % sp if sp > 1 else "<text:s/>")
        return "".join(out)

    def field(self, r):
        instr = (r.get("instr") or "").strip()
        word = instr.split(" ", 1)[0].upper() if instr else ""
        res = r.get("result")
        if isinstance(res, list):
            inner = []
            self.runs(res, inner)
            res_xml = "".join(inner)
            res_txt = "".join(x.get("text", "") for x in res if x.get("t") == "text")
        else:
            res_txt = res or ""
            res_xml = esc(res_txt)
        if word == "PAGE":
            return '<text:page-number text:select-page="current">%s</text:page-number>' % esc(res_txt or "1")
        if word in ("NUMPAGES", "SECTIONPAGES"):
            return '<text:page-count>%s</text:page-count>' % esc(res_txt or "1")
        if word == "DATE" or word == "CREATEDATE" or word == "SAVEDATE":
            return '<text:date>%s</text:date>' % esc(res_txt)
        if word == "TIME":
            return '<text:time>%s</text:time>' % esc(res_txt)
        if word == "TITLE":
            return '<text:title>%s</text:title>' % esc(res_txt)
        if word == "SUBJECT":
            return '<text:subject>%s</text:subject>' % esc(res_txt)
        if word == "AUTHOR":
            return '<text:initial-creator>%s</text:initial-creator>' % esc(res_txt)
        if word == "FILENAME":
            return '<text:file-name text:display="name-and-extension">%s</text:file-name>' % esc(res_txt)
        if word == "NUMWORDS":
            return '<text:word-count>%s</text:word-count>' % esc(res_txt)
        if word == "SEQ":
            name = instr.split()[1] if len(instr.split()) > 1 else "Figure"
            return '<text:sequence text:ref-name="ref%s%s" text:name="%s" text:formula="ooow:%s+1" style:num-format="1">%s</text:sequence>' % (
                esc(name), self.note_n, esc(name), esc(name), esc(res_txt))
        if word == "REF" and len(instr.split()) > 1:
            return '<text:bookmark-ref text:reference-format="text" text:ref-name="%s">%s</text:bookmark-ref>' % (
                esc(instr.split()[1]), esc(res_txt))
        return res_xml

    def annotation(self, cid):
        c = None
        for x in self.doc.comments:
            if x["id"] == cid:
                c = x
                break
        if c is None:
            return ""
        inner = []
        saved = self.in_styles
        self.blocks(c.get("blocks") or [B.para()], inner)
        self.in_styles = saved
        date = c.get("date") or datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
        return ('<office:annotation office:name="__Annotation__%d"><dc:creator>%s</dc:creator><dc:date>%s</dc:date>'
                '%s%s</office:annotation>' % (cid, esc(c.get("author") or ""), esc(date.rstrip("Z")),
                                              '<meta:creator-initials>%s</meta:creator-initials>' % esc(c["initials"]) if c.get("initials") else "",
                                              "".join(inner)))

    def image(self, r):
        self.pic_n += 1
        self.frame_n += 1
        ext = (r.get("ext") or "png").lower().replace("jpeg", "jpg")
        name = "Pictures/image%d.%s" % (self.pic_n, ext)
        self.pics[name] = r["data"]
        w = r["cx"] / B.EMU_PER_TWIP
        h = r["cy"] / B.EMU_PER_TWIP
        a = r.get("anchor")
        if a:
            wrap = {"square": "parallel", "tight": "parallel", "none": "run-through", "top": "none"}.get(a.get("wrap"), "parallel")
            gp = ['style:wrap="%s"' % wrap]
            if wrap == "run-through":
                gp.append('style:run-through="%s"' % ("background" if a.get("behind") else "foreground"))
            hrel = {"page": "page", "margin": "page-content", "column": "paragraph", "character": "char"}.get(a.get("hrel", "column"), "paragraph")
            vrel = {"page": "page", "margin": "page-content", "paragraph": "paragraph", "line": "line"}.get(a.get("vrel", "paragraph"), "paragraph")
            if a.get("halign"):
                gp.append('style:horizontal-pos="%s"' % {"inside": "inside", "outside": "outside"}.get(a["halign"], a["halign"]))
            else:
                gp.append('style:horizontal-pos="from-left"')
            gp.append('style:horizontal-rel="%s"' % hrel)
            if a.get("valign"):
                gp.append('style:vertical-pos="%s"' % {"center": "middle"}.get(a["valign"], a["valign"]))
            else:
                gp.append('style:vertical-pos="from-top"')
            gp.append('style:vertical-rel="%s"' % vrel)
            gs = self._auto("graphic", "<style:graphic-properties %s/>" % " ".join(gp), "fr", "Graphics")
            anchor = "page" if hrel == "page" and vrel == "page" else "char"
            pos = 'svg:x="%s" svg:y="%s" ' % (cm(a.get("x", 0) / B.EMU_PER_TWIP), cm(a.get("y", 0) / B.EMU_PER_TWIP))
        else:
            gs = self._auto("graphic", '<style:graphic-properties style:vertical-pos="top" style:vertical-rel="baseline"/>',
                            "fr", "Graphics")
            anchor = "as-char"
            pos = ""
        title = ""
        if r.get("descr"):
            title = "<svg:desc>%s</svg:desc>" % esc(r["descr"])
        return ('<draw:frame draw:style-name="%s" draw:name="%s" text:anchor-type="%s" %ssvg:width="%s" svg:height="%s" draw:z-index="%d">'
                '<draw:image xlink:href="%s" xlink:type="simple" xlink:show="embed" xlink:actuate="onLoad"/>%s</draw:frame>'
                % (gs, esc(r.get("name") or "Image%d" % self.frame_n), anchor, pos, cm(w), cm(h), self.frame_n, name, title))

    def paragraph(self, p, out, master=None):
        inner = []
        runs = p.get("runs") or []
        # a TOC field: its paragraphs are written as they are
        runs = [r for r in runs if r.get("t") not in ("fbegin", "fsep", "fend", "_ref", "_annref")]
        self.runs(runs, inner)
        body = "".join(inner)
        st = self.para_style(p, master)
        # page breaks inside a paragraph split it, as LibreOffice does
        parts = body.split("\x00PAGEBREAK\x00")
        sid = p.get("style") or "Normal"
        s = self.doc.style(sid)
        lvl = None
        if p.get("ppr", {}).get("outline") is not None:
            lvl = p["ppr"]["outline"] + 1
        elif s and sid.startswith("Heading") and sid[7:].isdigit():
            lvl = int(sid[7:])
        elif s:
            o = self.style_outline(sid)
            if o is not None:
                lvl = o + 1
        for i, part in enumerate(parts):
            pst = st
            if i > 0:
                pst = self._auto("paragraph", '<style:paragraph-properties fo:break-before="page"/>', "P", st if st else None) \
                    if not self.in_styles else st
            if lvl:
                out.append('<text:h text:style-name="%s" text:outline-level="%d">%s</text:h>' % (pst, lvl, part))
            else:
                out.append('<text:p text:style-name="%s">%s</text:p>' % (pst, part))

    def style_outline(self, sid, depth=0):
        s = self.doc.style(sid)
        if not s or depth > 10:
            return None
        if s.get("ppr", {}).get("outline") is not None:
            return s["ppr"]["outline"]
        return self.style_outline(s.get("based"), depth + 1) if s.get("based") else None

    def blocks(self, blocks, out, masters=None):
        i = 0
        n = len(blocks)
        while i < n:
            b = blocks[i]
            master = masters.pop(id(b), None) if masters else None
            if b.get("table"):
                out.append(self.table(b, master))
                i += 1
                continue
            num = (b.get("ppr") or {}).get("num")
            if num is not None and num[0] >= 0 and num[0] < len(self.doc.nums):
                j = i
                while j < n and not blocks[j].get("table") and (blocks[j].get("ppr") or {}).get("num") is not None \
                        and blocks[j]["ppr"]["num"][0] == num[0]:
                    j += 1
                self.list_xml(blocks[i:j], out, masters)
                i = j
                continue
            self.paragraph(b, out, master)
            i += 1

    def list_style(self, numi):
        ai, restart = self.doc.nums[numi]
        return "L%d" % (ai + 1)

    def list_xml(self, items, out, masters):
        numi = items[0]["ppr"]["num"][0]
        lname = self.list_style(numi)
        cont = numi in self.list_used
        self.list_used[numi] = True
        # nest by level
        out.append('<text:list text:style-name="%s"%s>' % (lname, ' text:continue-numbering="true"' if cont else ""))
        stack = [0]
        open_item = [False]
        for p in items:
            lvl = p["ppr"]["num"][1]
            while lvl > stack[-1]:
                if not open_item[-1]:
                    out.append("<text:list-item>")
                    open_item[-1] = True
                out.append("<text:list>")
                stack.append(stack[-1] + 1)
                open_item.append(False)
            while lvl < stack[-1]:
                if open_item[-1]:
                    out.append("</text:list-item>")
                out.append("</text:list>")
                stack.pop()
                open_item.pop()
            if open_item[-1]:
                out.append("</text:list-item>")
            out.append("<text:list-item>")
            open_item[-1] = True
            self.paragraph(p, out, masters.pop(id(p), None) if masters else None)
        while stack:
            if open_item[-1]:
                out.append("</text:list-item>")
            out.append("</text:list>")
            stack.pop()
            open_item.pop()

    def table(self, t, master=None):
        self.tbl_n += 1
        tn = "Table%d" % self.tbl_n
        cols = t.get("cols") or []
        width = t.get("width") or sum(cols) or 9000
        tp = 'style:width="%s" table:align="%s"' % (cm(width), {"center": "center", "right": "right"}.get(t.get("align"), "margins" if not t.get("indent") else "left"))
        if t.get("indent"):
            tp += ' fo:margin-left="%s"' % cm(t["indent"])
        extra = ' style:master-page-name="%s"' % master if master else ""
        ts = self._auto("table", "<style:table-properties %s/>" % tp, "Tbl", None, extra)
        out = ['<table:table table:name="%s" table:style-name="%s">' % (tn, ts)]
        for c in cols:
            cs = self._auto("table-column", '<style:table-column-properties style:column-width="%s"/>' % cm(c), "TC")
            out.append('<table:table-column table:style-name="%s"/>' % cs)
        if not cols:
            ncol = max((sum(c.get("span", 1) for c in r["cells"]) for r in t["rows"]), default=1)
            out.append('<table:table-column table:number-columns-repeated="%d"/>' % ncol)
        # rows spanned by vertically merged cells
        grid = []
        for r in t["rows"]:
            g = []
            ci = 0
            for c in r["cells"]:
                g.append((ci, c))
                ci += c.get("span", 1)
            grid.append(g)
        rspan = {}
        for ri, g in enumerate(grid):
            for ci, c in g:
                if c.get("vmerge") == "restart":
                    n = 1
                    for rj in range(ri + 1, len(grid)):
                        hit = [x for x in grid[rj] if x[0] == ci and x[1].get("vmerge") == "cont"]
                        if hit:
                            n += 1
                        else:
                            break
                    rspan[(ri, ci)] = n
        tb = t.get("tborders") or {}
        header_open = False
        for ri, r in enumerate(t["rows"]):
            if r.get("header") and not header_open and ri == 0:
                out.append("<table:table-header-rows>")
                header_open = True
            elif header_open and not r.get("header"):
                out.append("</table:table-header-rows>")
                header_open = False
            rp = ""
            if r.get("height"):
                rp = "<style:table-row-properties %s=\"%s\"/>" % ("style:row-height" if r.get("exact") else "style:min-row-height", cm(r["height"]))
            rs = self._auto("table-row", rp, "TR") if rp else None
            out.append('<table:table-row%s>' % (' table:style-name="%s"' % rs if rs else ""))
            nrows = len(t["rows"])
            for ci, c in grid[ri]:
                span = c.get("span", 1)
                if c.get("vmerge") == "cont":
                    out.append("<table:covered-table-cell/>" * span)
                    continue
                cp = []
                if c.get("shd"):
                    cp.append('fo:background-color="#%s"' % c["shd"].lower())
                cb = c.get("borders") or {}
                for side, inside in (("top", "insideH"), ("bottom", "insideH"), ("left", "insideV"), ("right", "insideV")):
                    edge = (side == "top" and ri == 0) or (side == "bottom" and ri == nrows - 1) or \
                        (side == "left" and ci == 0) or (side == "right" and ci + span >= max(1, len(cols) or ci + span))
                    v = cb.get(side, "unset")
                    if v == "unset":
                        v = tb.get(side if edge else inside, "unset")
                    if v == "unset":
                        v = (4, "000000", "single", 0) if t.get("borders", True) and not tb and not t.get("style") else None
                    if v:
                        sz, color, kind, _ = v
                        cp.append('fo:border-%s="%.2fpt %s #%s"' % (side, max(0.25, sz / 8.0), "double" if kind == "double" else "solid", (color or "000000").lower()))
                    else:
                        cp.append('fo:border-%s="none"' % side)
                cp.append('fo:padding-left="0.19cm" fo:padding-right="0.19cm" fo:padding-top="0cm" fo:padding-bottom="0cm"')
                if c.get("valign"):
                    cp.append('style:vertical-align="%s"' % {"center": "middle"}.get(c["valign"], c["valign"]))
                cs = self._auto("table-cell", "<style:table-cell-properties %s/>" % " ".join(cp), "TD")
                attrs = ' table:style-name="%s" office:value-type="string"' % cs
                if span > 1:
                    attrs += ' table:number-columns-spanned="%d"' % span
                n = rspan.get((ri, ci), 1)
                if n > 1:
                    attrs += ' table:number-rows-spanned="%d"' % n
                inner = []
                self.blocks(c.get("blocks") or [B.para()], inner)
                out.append("<table:table-cell%s>%s</table:table-cell>" % (attrs, "".join(inner)))
                if span > 1:
                    out.append("<table:covered-table-cell/>" * (span - 1))
            out.append("</table:table-row>")
        if header_open:
            out.append("</table:table-header-rows>")
        out.append("</table:table>")
        return "".join(out)

    # ---------------------------------------------------------- package
    def list_styles_xml(self):
        out = []
        for ai, levels in enumerate(self.doc.lists):
            out.append('<text:list-style style:name="L%d">' % (ai + 1))
            for li, lv in enumerate(levels[:10]):
                ind = lv.get("ind", 720 * (li + 1))
                hang = lv.get("hang", 360)
                props = ('<style:list-level-properties text:list-level-position-and-space-mode="label-alignment">'
                         '<style:list-level-label-alignment text:label-followed-by="listtab" text:list-tab-stop-position="%s" '
                         'fo:text-indent="%s" fo:margin-left="%s"/></style:list-level-properties>' % (cm(ind), cm(-hang), cm(ind)))
                if lv.get("fmt") == "bullet":
                    ch = (lv.get("text") or "•")[:1] or "•"
                    if 0xF000 <= ord(ch) <= 0xF0FF:
                        ch = chr(ord(ch) - 0xF000)
                    if (lv.get("font") in ("Symbol", "Wingdings", "Wingdings 2", "Wingdings 3") and ord(ch) < 0x100) or ord(ch) < 0x20:
                        ch = {"·": "•", "o": "◦", "§": "▪", "Ø": "➢", "v": "❖",
                              "ü": "✔", "q": "❏", "n": "■"}.get(ch, "•")
                    out.append('<text:list-level-style-bullet text:level="%d" text:bullet-char="%s">%s</text:list-level-style-bullet>'
                               % (li + 1, esc(ch), props))
                else:
                    text = lv.get("text") or ""
                    import re
                    m = list(re.finditer(r"%(\d)", text))
                    prefix = text[:m[0].start()] if m else text
                    suffix = text[m[-1].end():] if m else ""
                    disp = len(m) if m else 1
                    fmt = NUM_FMT.get(lv.get("fmt"), "1")
                    out.append('<text:list-level-style-number text:level="%d" style:num-prefix="%s" style:num-suffix="%s" '
                               'style:num-format="%s"%s%s>%s</text:list-level-style-number>' % (
                                   li + 1, esc(prefix), esc(suffix), fmt,
                                   ' text:display-levels="%d"' % disp if disp > 1 else "",
                                   ' text:start-value="%d"' % lv["start"] if lv.get("start", 1) != 1 else "", props))
            out.append('</text:list-style>')
        return "".join(out)

    def named_styles_xml(self):
        d = self.doc
        out = []
        dr = d.defaults.get("rpr") or {}
        dp = d.defaults.get("ppr") or {}
        pa, _ = para_attrs(dp)
        out.append('<style:default-style style:family="paragraph"><style:paragraph-properties style:tab-stop-distance="%s" %s/>'
                   '<style:text-properties %s/></style:default-style>' % (cm(d.tab_stop or 720), pa,
                                                                         text_attrs(dict({"sz": 20}, **dr), self.fonts)))
        out.append('<style:style style:name="Graphics" style:family="graphic"><style:graphic-properties '
                   'text:anchor-type="paragraph" svg:x="0cm" svg:y="0cm" style:wrap="dynamic" style:number-wrapped-paragraphs="no-limit" '
                   'style:vertical-pos="top" style:vertical-rel="paragraph" style:horizontal-pos="center" style:horizontal-rel="paragraph"/></style:style>')
        have_std = False
        for s in d.styles:
            if s["type"] not in ("paragraph", "character"):
                continue
            fam = "paragraph" if s["type"] == "paragraph" else "text"
            name = self.sname(s["id"])
            disp = ODF_NAME.get(s["id"]) or ODF_NAME.get(B.style_id(s.get("name") or "")) or s.get("name") or s["id"]
            if name == "Standard":
                disp = "Standard"
            if name == "Standard":
                have_std = True
            body = ""
            if fam == "paragraph":
                pa, inner = para_attrs({k: v for k, v in (s.get("ppr") or {}).items() if k not in ("num",)})
                if pa or inner:
                    body += "<style:paragraph-properties %s>%s</style:paragraph-properties>" % (pa, inner)
            ta = text_attrs(s.get("rpr") or {}, self.fonts)
            if ta:
                body += "<style:text-properties %s/>" % ta
            parent = s.get("based")
            attrs = ' style:display-name="%s"' % esc(disp) if enc(disp) != disp else ""
            if parent and parent != s["id"] and d.style(parent):
                attrs += ' style:parent-style-name="%s"' % self.sname(parent)
            if s.get("next") and d.style(s["next"]):
                attrs += ' style:next-style-name="%s"' % self.sname(s["next"])
            o = (s.get("ppr") or {}).get("outline")
            if fam == "paragraph" and o is not None:
                attrs += ' style:default-outline-level="%d"' % (o + 1)
            out.append('<style:style style:name="%s" style:family="%s"%s>%s</style:style>' % (name, fam, attrs, body))
        out.append('<style:style style:name="Footnote_20_anchor" style:display-name="Footnote anchor" style:family="text">'
                   '<style:text-properties style:text-position="super 58%"/></style:style>'
                   '<style:style style:name="Footnote_20_Symbol" style:display-name="Footnote Symbol" style:family="text">'
                   '<style:text-properties style:text-position="super 58%"/></style:style>')
        if not have_std:
            out.append('<style:style style:name="Standard" style:family="paragraph" style:class="text"/>')
        return "".join(out)

    def page_layout(self, i, s):
        m = s["margins"]
        hdr = bool(s.get("headers"))
        ftr = bool(s.get("footers"))
        top = m.get("header", 720) if hdr else m["top"]
        bottom = m.get("footer", 720) if ftr else m["bottom"]
        cols = ""
        if s.get("cols", 1) > 1:
            cols = '<style:columns fo:column-count="%d" fo:column-gap="%s"/>' % (s["cols"], cm(s.get("col_space", 720)))
        out = ['<style:page-layout style:name="pm%d"><style:page-layout-properties fo:page-width="%s" fo:page-height="%s" '
               'style:print-orientation="%s" fo:margin-top="%s" fo:margin-bottom="%s" fo:margin-left="%s" fo:margin-right="%s" '
               'style:num-format="1" style:writing-mode="lr-tb">%s</style:page-layout-properties>' % (
                   i, cm(s["w"]), cm(s["h"]), "landscape" if s.get("landscape") else "portrait", cm(top), cm(bottom),
                   cm(m["left"]), cm(m["right"]), cols)]
        if hdr:
            gap = max(0, m["top"] - m.get("header", 720))
            out.append('<style:header-style><style:header-footer-properties fo:min-height="%s" fo:margin-bottom="0cm" '
                       'style:dynamic-spacing="true"/></style:header-style>' % cm(gap))
        else:
            out.append("<style:header-style/>")
        if ftr:
            gap = max(0, m["bottom"] - m.get("footer", 720))
            out.append('<style:footer-style><style:header-footer-properties fo:min-height="%s" fo:margin-top="0cm" '
                       'style:dynamic-spacing="true"/></style:footer-style>' % cm(gap))
        else:
            out.append("<style:footer-style/>")
        out.append("</style:page-layout>")
        return "".join(out)

    def master(self, i, s, name):
        out = ['<style:master-page style:name="%s" style:page-layout-name="pm%d">' % (name, i)]
        self.in_styles = True
        for kind, store in (("header", s.get("headers") or {}), ("footer", s.get("footers") or {})):
            if "default" in store or "first" in store or "even" in store:
                main = store.get("default") or [B.para()]
                inner = []
                self.blocks(main, inner)
                out.append("<style:%s>%s</style:%s>" % (kind, "".join(inner), kind))
                if "even" in store:
                    inner = []
                    self.blocks(store["even"], inner)
                    out.append("<style:%s-left>%s</style:%s-left>" % (kind, "".join(inner), kind))
                if s.get("title_pg"):
                    inner = []
                    self.blocks(store.get("first") or [B.para()], inner)
                    out.append("<style:%s-first>%s</style:%s-first>" % (kind, "".join(inner), kind))
        self.in_styles = False
        out.append("</style:master-page>")
        return "".join(out)

    def build(self):
        d = self.doc
        secs = d.sections or [B.section()]
        body = []
        masters = {}
        names = []
        for i, s in enumerate(secs):
            names.append("Standard" if i == 0 else "MP%d" % i)
        # the first block of each later section starts its page style
        first_of = {}
        for i, s in enumerate(secs):
            if s["blocks"]:
                b0 = s["blocks"][0]
                if i > 0 or True:
                    first_of[id(b0)] = names[i]
        prev_cols = None
        for i, s in enumerate(secs):
            blocks = s["blocks"]
            same_page = i > 0 and s.get("break") == "continuous"
            if same_page:
                # a continuous break: a section with its own columns on the same page
                first_of.pop(id(blocks[0]) if blocks else None, None)
                if s.get("cols", 1) > 1:
                    sect = self._auto("section", '<style:section-properties><style:columns fo:column-count="%d" fo:column-gap="%s"/>'
                                                 '</style:section-properties>' % (s["cols"], cm(s.get("col_space", 720))), "Sect")
                    body.append('<text:section text:style-name="%s" text:name="Section%d">' % (sect, i))
                    self.blocks(blocks, body, first_of)
                    body.append('</text:section>')
                    continue
            self.blocks(blocks, body, first_of)
            prev_cols = s.get("cols")
        body_xml = "".join(body)
        # styles.xml (built after the body so fonts are known)
        self.in_styles = True
        named = self.named_styles_xml()
        lists = self.list_styles_xml()
        self.in_styles = False
        layouts = "".join(self.page_layout(i, s) for i, s in enumerate(secs))
        mastersx = "".join(self.master(i, s, names[i]) for i, s in enumerate(secs))
        fonts = "".join('<style:font-face style:name="%s" svg:font-family="%s"/>' % (esc(f), esc(_quote(f)))
                        for f in sorted(self.fonts))
        styles = (HDR + '<office:document-styles %s><office:font-face-decls>%s</office:font-face-decls>'
                  '<office:styles>%s%s<text:notes-configuration text:note-class="footnote" text:citation-style-name="Footnote_20_Symbol" text:citation-body-style-name="Footnote_20_anchor" style:num-format="1" text:start-value="0" '
                  'text:footnotes-position="page" text:start-numbering-at="document"/>'
                  '<text:notes-configuration text:note-class="endnote" text:citation-style-name="Footnote_20_Symbol" text:citation-body-style-name="Footnote_20_anchor" style:num-format="i" text:start-value="0"/></office:styles>'
                  '<office:automatic-styles>%s%s</office:automatic-styles><office:master-styles>%s</office:master-styles>'
                  '</office:document-styles>' % (NSDECL, fonts, named, lists, layouts, "".join(self.sauto_xml), mastersx))
        content = (HDR + '<office:document-content %s><office:font-face-decls>%s</office:font-face-decls>'
                   '<office:automatic-styles>%s</office:automatic-styles><office:body><office:text>%s</office:text>'
                   '</office:body></office:document-content>' % (NSDECL, fonts, "".join(self.auto_xml), body_xml or '<text:p/>'))
        m = d.meta
        now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
        metax = []
        for k, tag in (("title", "dc:title"), ("subject", "dc:subject"), ("description", "dc:description")):
            if m.get(k):
                metax.append("<%s>%s</%s>" % (tag, esc(m[k]), tag))
        if m.get("creator"):
            metax.append("<meta:initial-creator>%s</meta:initial-creator>" % esc(m["creator"]))
        if m.get("keywords"):
            for kw in [k.strip() for k in m["keywords"].replace(";", ",").split(",") if k.strip()]:
                metax.append("<meta:keyword>%s</meta:keyword>" % esc(kw))
        metax.append("<meta:creation-date>%s</meta:creation-date><dc:date>%s</dc:date>"
                     "<meta:generator>Folio Writer</meta:generator>" % (esc((m.get("created") or now).rstrip("Z")), now))
        meta = HDR + '<office:document-meta %s><office:meta>%s</office:meta></office:document-meta>' % (NSDECL, "".join(metax))
        settings = (HDR + '<office:document-settings xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
                    'xmlns:config="urn:oasis:names:tc:opendocument:xmlns:config:1.0" office:version="1.3"><office:settings>'
                    '<config:config-item-set config:name="ooo:configuration-settings">'
                    '<config:config-item config:name="TabsRelativeToIndent" config:type="boolean">false</config:config-item>'
                    '<config:config-item config:name="AddParaTableSpacingAtStart" config:type="boolean">false</config:config-item>'
                    '</config:config-item-set></office:settings></office:document-settings>')
        manifest = ['<?xml version="1.0" encoding="UTF-8"?>\n<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0" manifest:version="1.3">'
                    '<manifest:file-entry manifest:full-path="/" manifest:version="1.3" manifest:media-type="application/vnd.oasis.opendocument.text"/>']
        for n in ("content.xml", "styles.xml", "meta.xml", "settings.xml"):
            manifest.append('<manifest:file-entry manifest:full-path="%s" manifest:media-type="text/xml"/>' % n)
        mt = {"png": "image/png", "jpg": "image/jpeg", "gif": "image/gif", "bmp": "image/bmp", "emf": "image/x-emf",
              "wmf": "image/x-wmf", "tif": "image/tiff", "svg": "image/svg+xml"}
        for n in self.pics:
            manifest.append('<manifest:file-entry manifest:full-path="%s" manifest:media-type="%s"/>' % (
                n, mt.get(n.rsplit(".", 1)[-1], "application/octet-stream")))
        manifest.append('</manifest:manifest>')
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr(zipfile.ZipInfo("mimetype"), "application/vnd.oasis.opendocument.text", compress_type=zipfile.ZIP_STORED)
            z.writestr("content.xml", content)
            z.writestr("styles.xml", styles)
            z.writestr("meta.xml", meta)
            z.writestr("settings.xml", settings)
            for n, data in self.pics.items():
                z.writestr(n, data)
            z.writestr("META-INF/manifest.xml", "".join(manifest))
        return buf.getvalue()


def _quote(f):
    return "'%s'" % f if " " in f else f


def to_odt(doc):
    return Writer(doc).build()


def docx_to_odt(docx_path, odt_path):
    import sys
    from . import docxread
    sys.setrecursionlimit(max(sys.getrecursionlimit(), 20000))
    data = to_odt(docxread.read(docx_path))
    with open(odt_path, "wb") as fh:
        fh.write(data)
    return True
