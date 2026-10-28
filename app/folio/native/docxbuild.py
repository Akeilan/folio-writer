"""A small document model shared by Folio's own file readers and writers
(OpenDocument text, Word 97-2003), and the .docx package written from it.

Lengths are twips (1/20 pt) unless named otherwise; font sizes are half points;
colours are "RRGGBB".

Doc
  styles    [Style]           paragraph / character / table styles
  defaults  {"rpr": {}, "ppr": {}}
  lists     [[Level]]         abstract numbering definitions
  nums      [(list index, restart)]  list instances; ppr["num"] = (num index, level)
  sections  [Section]         each with its own blocks
  comments  [{"id", "author", "initials", "date", "blocks"}]
  meta      {"title", "subject", "creator", "keywords", "description"}
Section: w, h, landscape, margins {top right bottom left header footer gutter},
  headers / footers {"default"|"first"|"even": blocks}, title_pg, cols, col_space, blocks
Block: a paragraph {"style", "ppr", "rpr", "runs"} or a table {"table": True, ...}
Run: {"t": "text"|"tab"|"br"|"page"|"col"|"image"|"note"|"field"|"link"|"cstart"|"cend"|
      "bmstart"|"bmend", ...}
"""
import datetime
import io
import zipfile
from xml.sax.saxutils import escape as _esc

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
HDR = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n'
NSDECL = ('xmlns:w="%s" xmlns:r="%s" '
          'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
          'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
          'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture" '
          'xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" '
          'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" '
          'mc:Ignorable="w14"' % (W_NS, R_NS))
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"
EMU_PER_TWIP = 635

# built-in style ids by display name, as Word names them
BUILTIN = {"Normal": "Normal", "Title": "Title", "Subtitle": "Subtitle", "Quote": "Quote",
           "Intense Quote": "IntenseQuote", "List Paragraph": "ListParagraph",
           "No Spacing": "NoSpacing", "Caption": "Caption", "Header": "Header",
           "Footer": "Footer", "Footnote Text": "FootnoteText", "Endnote Text": "EndnoteText",
           "Body Text": "BodyText", "Hyperlink": "Hyperlink", "Strong": "Strong",
           "Emphasis": "Emphasis", "Table Grid": "TableGrid", "TOC Heading": "TOCHeading",
           "Comment Text": "CommentText", "Footnote Reference": "FootnoteReference",
           "Endnote Reference": "EndnoteReference", "Default Paragraph Font": "DefaultParagraphFont",
           "Normal Table": "TableNormal", "No List": "NoList", "List Bullet": "ListBullet",
           "List Number": "ListNumber", "Plain Text": "PlainText", "Signature": "Signature",
           "Book Title": "BookTitle", "Subtle Emphasis": "SubtleEmphasis",
           "Intense Emphasis": "IntenseEmphasis", "Index 1": "Index1", "Table of Figures":
           "TableofFigures", "Annotation Text": "CommentText"}
for _n in range(1, 10):
    BUILTIN["Heading %d" % _n] = "Heading%d" % _n
    BUILTIN["TOC %d" % _n] = "TOC%d" % _n
# names Word writes in lower case in styles.xml
LOWER = {"Heading%d" % n: "heading %d" % n for n in range(1, 10)}
LOWER.update({"TOC%d" % n: "toc %d" % n for n in range(1, 10)})
LOWER.update({"Caption": "caption", "Header": "header", "Footer": "footer",
              "FootnoteText": "footnote text", "EndnoteText": "endnote text",
              "CommentText": "annotation text", "FootnoteReference": "footnote reference",
              "EndnoteReference": "endnote reference", "TableNormal": "Normal Table",
              "Index1": "index 1", "TableofFigures": "table of figures"})


def esc(s):
    return _esc(str(s), {'"': "&quot;"})


def style_id(name):
    """Word's style id for a display name."""
    if name in BUILTIN:
        return BUILTIN[name]
    sid = "".join(c for c in name if c.isalnum())
    return sid or "Style"


class Doc:
    def __init__(self):
        self.styles = []
        self.defaults = {"rpr": {}, "ppr": {}}
        self.lists = []
        self.nums = []
        self.sections = []
        self.comments = []
        self.meta = {}
        self.tab_stop = 720

    def style(self, sid):
        for s in self.styles:
            if s["id"] == sid:
                return s
        return None

    def add_style(self, sid, name, kind="paragraph", based=None, nxt=None, ppr=None, rpr=None,
                  default=False):
        s = self.style(sid)
        if s is None:
            s = {"id": sid, "name": name, "type": kind}
            self.styles.append(s)
        s.update({"name": name, "type": kind, "based": based, "next": nxt,
                  "ppr": dict(ppr or {}), "rpr": dict(rpr or {}), "default": default})
        return s

    def all_blocks(self):
        for sec in self.sections:
            yield from walk_blocks(sec["blocks"])


def walk_blocks(blocks):
    for b in blocks:
        if b.get("table"):
            for row in b["rows"]:
                for c in row["cells"]:
                    yield from walk_blocks(c["blocks"])
        else:
            yield b


def para(text="", style=None, ppr=None, rpr=None):
    runs = [{"t": "text", "text": text, "rpr": dict(rpr or {})}] if text else []
    return {"style": style, "ppr": dict(ppr or {}), "rpr": {}, "runs": runs}


def section():
    return {"w": 12240, "h": 15840, "landscape": False,
            "margins": {"top": 1440, "right": 1440, "bottom": 1440, "left": 1440,
                        "header": 720, "footer": 720, "gutter": 0},
            "headers": {}, "footers": {}, "title_pg": False, "cols": 1, "col_space": 720,
            "blocks": [], "break": "nextPage"}


# ------------------------------------------------------------------ properties
UNDERLINES = {"single", "double", "thick", "dotted", "dash", "dotDash", "dotDotDash", "wave",
              "words", "dottedHeavy", "dashLong", "wavyDouble"}


def rpr_xml(r, char_style=None):
    out = []
    if char_style:
        out.append('<w:rStyle w:val="%s"/>' % esc(char_style))
    f = r.get("font")
    if f or r.get("font_ea") or r.get("font_cs"):
        a = []
        if f:
            a.append('w:ascii="%s" w:hAnsi="%s"' % (esc(f), esc(f)))
        if r.get("font_ea"):
            a.append('w:eastAsia="%s"' % esc(r["font_ea"]))
        if r.get("font_cs"):
            a.append('w:cs="%s"' % esc(r["font_cs"]))
        out.append('<w:rFonts %s/>' % " ".join(a))
    for k, tag in (("b", "b"), ("i", "i")):
        if k in r:
            out.append('<w:%s/>' % tag if r[k] else '<w:%s w:val="0"/>' % tag)
            out.append('<w:%sCs/>' % tag if r[k] else '<w:%sCs w:val="0"/>' % tag)
    for k, tag in (("caps", "caps"), ("smallcaps", "smallCaps"), ("strike", "strike"),
                   ("dstrike", "dstrike"), ("outline", "outline"), ("shadow", "shadow"),
                   ("emboss", "emboss"), ("imprint", "imprint"), ("hidden", "vanish")):
        if k in r:
            out.append('<w:%s/>' % tag if r[k] else '<w:%s w:val="0"/>' % tag)
    if r.get("color"):
        out.append('<w:color w:val="%s"/>' % r["color"])
    if r.get("spacing"):
        out.append('<w:spacing w:val="%d"/>' % r["spacing"])
    if r.get("scale") and r["scale"] != 100:
        out.append('<w:w w:val="%d"/>' % r["scale"])
    if r.get("position"):
        out.append('<w:position w:val="%d"/>' % r["position"])
    if r.get("sz"):
        out.append('<w:sz w:val="%d"/><w:szCs w:val="%d"/>' % (r["sz"], r["sz"]))
    if r.get("highlight"):
        out.append('<w:highlight w:val="%s"/>' % r["highlight"])
    if "u" in r:
        u = r["u"] if r["u"] in UNDERLINES else ("none" if not r["u"] else "single")
        out.append('<w:u w:val="%s"/>' % u)
    if r.get("shd"):
        out.append('<w:shd w:val="clear" w:color="auto" w:fill="%s"/>' % r["shd"])
    if r.get("vert"):
        out.append('<w:vertAlign w:val="%s"/>' % r["vert"])
    if r.get("lang"):
        out.append('<w:lang w:val="%s"/>' % esc(r["lang"]))
    return "<w:rPr>%s</w:rPr>" % "".join(out) if out else ""


def _border(side, b):
    sz, color, kind, space = b
    return '<w:%s w:val="%s" w:sz="%d" w:space="%d" w:color="%s"/>' % (
        side, kind or "single", sz, space or 0, color or "auto")


def ppr_xml(p, style=None, mark_rpr=None, sect=None):
    out = []
    if style:
        out.append('<w:pStyle w:val="%s"/>' % esc(style))
    if p.get("keep_next"):
        out.append('<w:keepNext/>')
    if p.get("keep_lines"):
        out.append('<w:keepLines/>')
    if p.get("pbb"):
        out.append('<w:pageBreakBefore/>')
    if "widow" in p:
        out.append('<w:widowControl/>' if p["widow"] else '<w:widowControl w:val="0"/>')
    if p.get("num") is not None:
        n, lvl = p["num"]
        out.append('<w:numPr><w:ilvl w:val="%d"/><w:numId w:val="%d"/></w:numPr>' % (lvl, n + 1 if n >= 0 else 0))
    if p.get("borders"):
        out.append('<w:pBdr>%s</w:pBdr>' % "".join(
            _border(s, p["borders"][s]) for s in ("top", "left", "bottom", "right", "between")
            if s in p["borders"]))
    if p.get("shd"):
        out.append('<w:shd w:val="clear" w:color="auto" w:fill="%s"/>' % p["shd"])
    if p.get("tabs"):
        t = []
        for pos, kind, leader in p["tabs"]:
            t.append('<w:tab w:val="%s"%s w:pos="%d"/>' % (
                kind, ' w:leader="%s"' % leader if leader and leader != "none" else "", pos))
        out.append('<w:tabs>%s</w:tabs>' % "".join(t))
    if p.get("bidi"):
        out.append('<w:bidi/>')
    sp = []
    if "sb" in p:
        sp.append('w:before="%d"' % p["sb"])
    if "sa" in p:
        sp.append('w:after="%d"' % p["sa"])
    if "line" in p:
        sp.append('w:line="%d" w:lineRule="%s"' % (p["line"], p.get("line_rule", "auto")))
    if p.get("contextual"):
        pass
    if sp:
        out.append('<w:spacing %s/>' % " ".join(sp))
    if p.get("contextual"):
        out.append('<w:contextualSpacing/>')
    ind = []
    if "ind_l" in p:
        ind.append('w:left="%d"' % p["ind_l"])
    if "ind_r" in p:
        ind.append('w:right="%d"' % p["ind_r"])
    if p.get("ind_first", 0) > 0:
        ind.append('w:firstLine="%d"' % p["ind_first"])
    elif p.get("ind_first", 0) < 0:
        ind.append('w:hanging="%d"' % -p["ind_first"])
    elif "ind_first" in p:
        ind.append('w:firstLine="0"')
    if ind:
        out.append('<w:ind %s/>' % " ".join(ind))
    if p.get("align"):
        out.append('<w:jc w:val="%s"/>' % p["align"])
    if p.get("outline") is not None:
        out.append('<w:outlineLvl w:val="%d"/>' % p["outline"])
    if mark_rpr:
        out.append(rpr_xml(mark_rpr))
    if sect:
        out.append(sect)
    return "<w:pPr>%s</w:pPr>" % "".join(out) if out else ""


# ------------------------------------------------------------------- writer
class _Part:
    """A story (body, header, note...) being written: its relationships."""

    def __init__(self, pkg, name):
        self.pkg = pkg
        self.name = name
        self.rels = []

    def rel(self, kind, target, external=False):
        for rid, k, t, e in self.rels:
            if k == kind and t == target:
                return rid
        rid = "rId%d" % (len(self.rels) + 100)
        self.rels.append((rid, kind, target, external))
        return rid

    def rels_xml(self, base=()):
        out = [HDR, '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">']
        for rid, kind, target in base:
            out.append('<Relationship Id="%s" Type="%s%s" Target="%s"/>' % (rid, REL, kind, target))
        for rid, kind, target, ext in self.rels:
            out.append('<Relationship Id="%s" Type="%s%s" Target="%s"%s/>' % (
                rid, REL, kind, esc(target), ' TargetMode="External"' if ext else ""))
        out.append('</Relationships>')
        return "".join(out)


class _Writer:
    def __init__(self, doc):
        self.doc = doc
        self.files = {}
        self.media = 0
        self.media_types = set()
        self.footnotes = []
        self.endnotes = []
        self.obj_id = 1
        self.bm_id = 0
        self.bm_ids = {}
        self.headers = 0
        self.footers = 0
        self.overrides = []

    # ---- runs
    def runs(self, part, runs, out):
        for r in runs:
            t = r["t"]
            rp = rpr_xml(r.get("rpr", {}), r.get("cstyle"))
            if t == "text":
                if not r["text"]:
                    continue
                txt = r["text"]
                # tabs and line breaks inside a text run
                pieces = []
                cur = ""
                for ch in txt:
                    if ch == "\t":
                        pieces.append(("t", cur))
                        pieces.append(("tab", ""))
                        cur = ""
                    elif ch == "\n" or ch == "\x0b":
                        pieces.append(("t", cur))
                        pieces.append(("br", ""))
                        cur = ""
                    else:
                        cur += ch
                pieces.append(("t", cur))
                body = []
                for k, s in pieces:
                    if k == "t" and s:
                        body.append('<w:t xml:space="preserve">%s</w:t>' % esc(_clean(s)))
                    elif k == "tab":
                        body.append('<w:tab/>')
                    elif k == "br":
                        body.append('<w:br/>')
                if body:
                    out.append('<w:r>%s%s</w:r>' % (rp, "".join(body)))
            elif t == "tab":
                out.append('<w:r>%s<w:tab/></w:r>' % rp)
            elif t == "br":
                out.append('<w:r>%s<w:br/></w:r>' % rp)
            elif t == "page":
                out.append('<w:r>%s<w:br w:type="page"/></w:r>' % rp)
            elif t == "col":
                out.append('<w:r>%s<w:br w:type="column"/></w:r>' % rp)
            elif t == "image":
                out.append('<w:r>%s%s</w:r>' % (rp, self.image(part, r)))
            elif t == "note":
                lst = self.footnotes if r.get("kind") != "endnote" else self.endnotes
                nid = len(lst) + 1
                lst.append(r["blocks"])
                tag = "footnoteReference" if r.get("kind") != "endnote" else "endnoteReference"
                st = "FootnoteReference" if tag == "footnoteReference" else "EndnoteReference"
                out.append('<w:r>%s<w:%s w:id="%d"/></w:r>' % (
                    rpr_xml(r.get("rpr", {}), st), tag, nid))
            elif t == "field":
                instr = r["instr"]
                res = r.get("result", "")
                out.append('<w:r>%s<w:fldChar w:fldCharType="begin"/></w:r>' % rp)
                out.append('<w:r>%s<w:instrText xml:space="preserve"> %s </w:instrText></w:r>' % (rp, esc(instr)))
                out.append('<w:r>%s<w:fldChar w:fldCharType="separate"/></w:r>' % rp)
                if isinstance(res, list):
                    self.runs(part, res, out)
                elif res:
                    out.append('<w:r>%s<w:t xml:space="preserve">%s</w:t></w:r>' % (rp, esc(_clean(res))))
                out.append('<w:r>%s<w:fldChar w:fldCharType="end"/></w:r>' % rp)
            elif t == "fbegin":
                out.append('<w:r>%s<w:fldChar w:fldCharType="begin"/></w:r>' % rp)
                out.append('<w:r>%s<w:instrText xml:space="preserve"> %s </w:instrText></w:r>' % (rp, esc(r["instr"])))
            elif t == "fsep":
                out.append('<w:r>%s<w:fldChar w:fldCharType="separate"/></w:r>' % rp)
            elif t == "fend":
                out.append('<w:r>%s<w:fldChar w:fldCharType="end"/></w:r>' % rp)
            elif t == "link":
                inner = []
                self.runs(part, r["runs"], inner)
                if r.get("url"):
                    rid = part.rel("hyperlink", r["url"], external=True)
                    out.append('<w:hyperlink r:id="%s" w:history="1">%s</w:hyperlink>' % (rid, "".join(inner)))
                elif r.get("anchor"):
                    out.append('<w:hyperlink w:anchor="%s" w:history="1">%s</w:hyperlink>' % (
                        esc(r["anchor"]), "".join(inner)))
                else:
                    out.extend(inner)
            elif t == "cstart":
                out.append('<w:commentRangeStart w:id="%d"/>' % r["id"])
            elif t == "cend":
                out.append('<w:commentRangeEnd w:id="%d"/>' % r["id"])
                out.append('<w:r><w:rPr><w:rStyle w:val="CommentReference"/></w:rPr>'
                           '<w:commentReference w:id="%d"/></w:r>' % r["id"])
            elif t == "bmstart":
                bid = self.bm_ids.setdefault(r["name"], len(self.bm_ids))
                out.append('<w:bookmarkStart w:id="%d" w:name="%s"/>' % (bid, esc(r["name"][:40])))
            elif t == "bmend":
                bid = self.bm_ids.setdefault(r["name"], len(self.bm_ids))
                out.append('<w:bookmarkEnd w:id="%d"/>' % bid)

    def image(self, part, r):
        self.media += 1
        ext = (r.get("ext") or "png").lower().replace("jpeg", "jpg")
        name = "media/image%d.%s" % (self.media, ext)
        self.files["word/" + name] = r["data"]
        self.media_types.add(ext)
        rid = part.rel("image", name)
        cx, cy = int(r["cx"]), int(r["cy"])
        oid = self.obj_id
        self.obj_id += 1
        nm = esc(r.get("name") or "Picture %d" % oid)
        descr = esc(r.get("descr", ""))
        graphic = ('<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
                   '<pic:pic><pic:nvPicPr><pic:cNvPr id="%d" name="%s" descr="%s"/><pic:cNvPicPr/></pic:nvPicPr>'
                   '<pic:blipFill><a:blip r:embed="%s"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
                   '<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="%d" cy="%d"/></a:xfrm>'
                   '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic>'
                   % (oid, nm, descr, rid, cx, cy))
        if r.get("anchor"):
            a = r["anchor"]
            wrap = {"square": '<wp:wrapSquare wrapText="bothSides"/>', "none": '<wp:wrapNone/>',
                    "top": '<wp:wrapTopAndBottom/>', "tight": '<wp:wrapSquare wrapText="bothSides"/>'}.get(
                a.get("wrap", "square"), '<wp:wrapSquare wrapText="bothSides"/>')
            return ('<w:drawing><wp:anchor distT="0" distB="0" distL="114300" distR="114300" simplePos="0" '
                    'relativeHeight="%d" behindDoc="%d" locked="0" layoutInCell="1" allowOverlap="1">'
                    '<wp:simplePos x="0" y="0"/>'
                    '<wp:positionH relativeFrom="%s">%s</wp:positionH>'
                    '<wp:positionV relativeFrom="%s">%s</wp:positionV>'
                    '<wp:extent cx="%d" cy="%d"/><wp:effectExtent l="0" t="0" r="0" b="0"/>%s'
                    '<wp:docPr id="%d" name="%s" descr="%s"/><wp:cNvGraphicFramePr/>%s</wp:anchor></w:drawing>'
                    % (251659264 + oid, 1 if a.get("behind") else 0, a.get("hrel", "column"),
                       "<wp:align>%s</wp:align>" % a["halign"] if a.get("halign") else "<wp:posOffset>%d</wp:posOffset>" % int(a.get("x", 0)),
                       a.get("vrel", "paragraph"),
                       "<wp:align>%s</wp:align>" % a["valign"] if a.get("valign") else "<wp:posOffset>%d</wp:posOffset>" % int(a.get("y", 0)),
                       cx, cy, wrap, oid, nm, descr, graphic))
        return ('<w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0">'
                '<wp:extent cx="%d" cy="%d"/><wp:effectExtent l="0" t="0" r="0" b="0"/>'
                '<wp:docPr id="%d" name="%s" descr="%s"/><wp:cNvGraphicFramePr>'
                '<a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr>%s</wp:inline></w:drawing>'
                % (cx, cy, oid, nm, descr, graphic))

    # ---- blocks
    def blocks(self, part, blocks, out, last_sect=None):
        n = len(blocks)
        if n == 0:
            out.append('<w:p>%s</w:p>' % (ppr_xml({}, sect=last_sect) if last_sect else ""))
            return
        for i, b in enumerate(blocks):
            is_last = i == n - 1
            if b.get("table"):
                self.table(part, b, out)
                if is_last and last_sect:
                    out.append('<w:p>%s</w:p>' % ppr_xml({}, sect=last_sect))
                continue
            inner = []
            self.runs(part, b.get("runs", []), inner)
            out.append('<w:p>%s%s</w:p>' % (
                ppr_xml(b.get("ppr", {}), b.get("style"), b.get("rpr"),
                        last_sect if is_last else None), "".join(inner)))

    def table(self, part, t, out):
        cols = t.get("cols") or []
        tp = []
        if t.get("style"):
            tp.append('<w:tblStyle w:val="%s"/>' % esc(t["style"]))
        total = sum(cols) if cols else 0
        if t.get("width"):
            tp.append('<w:tblW w:w="%d" w:type="dxa"/>' % t["width"])
        elif total:
            tp.append('<w:tblW w:w="%d" w:type="dxa"/>' % total)
        else:
            tp.append('<w:tblW w:w="0" w:type="auto"/>')
        if t.get("align"):
            tp.append('<w:jc w:val="%s"/>' % t["align"])
        if t.get("indent"):
            tp.append('<w:tblInd w:w="%d" w:type="dxa"/>' % t["indent"])
        if t.get("borders", True) and not t.get("style"):
            b = '<w:%s w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
            tp.append('<w:tblBorders>%s</w:tblBorders>' % "".join(
                b % s for s in ("top", "left", "bottom", "right", "insideH", "insideV")))
        tp.append('<w:tblLayout w:type="fixed"/>' if cols else "")
        tp.append('<w:tblLook w:val="04A0" w:firstRow="1" w:lastRow="0" w:firstColumn="1" '
                  'w:lastColumn="0" w:noHBand="0" w:noVBand="1"/>')
        out.append('<w:tbl><w:tblPr>%s</w:tblPr>' % "".join(tp))
        if not cols:
            ncol = max((sum(c.get("span", 1) for c in r["cells"]) for r in t["rows"]), default=1)
            cols = [9360 // max(1, ncol)] * ncol
        out.append('<w:tblGrid>%s</w:tblGrid>' % "".join('<w:gridCol w:w="%d"/>' % c for c in cols))
        for row in t["rows"]:
            trp = []
            if row.get("header"):
                trp.append('<w:tblHeader/>')
            if row.get("height"):
                trp.append('<w:trHeight w:val="%d"%s/>' % (row["height"], ' w:hRule="exact"' if row.get("exact") else ""))
            if row.get("cant_split"):
                trp.append('<w:cantSplit/>')
            out.append('<w:tr>%s' % ('<w:trPr>%s</w:trPr>' % "".join(trp) if trp else ""))
            ci = 0
            for c in row["cells"]:
                span = c.get("span", 1)
                w = c.get("width") or sum(cols[ci:ci + span]) if cols else 0
                ci += span
                cp = ['<w:tcW w:w="%d" w:type="dxa"/>' % w]
                if span > 1:
                    cp.append('<w:gridSpan w:val="%d"/>' % span)
                if c.get("vmerge") == "restart":
                    cp.append('<w:vMerge w:val="restart"/>')
                elif c.get("vmerge") == "cont":
                    cp.append('<w:vMerge/>')
                if c.get("borders"):
                    cp.append('<w:tcBorders>%s</w:tcBorders>' % "".join(
                        _border(s, c["borders"][s]) for s in ("top", "left", "bottom", "right") if s in c["borders"]))
                if c.get("shd"):
                    cp.append('<w:shd w:val="clear" w:color="auto" w:fill="%s"/>' % c["shd"])
                if c.get("valign"):
                    cp.append('<w:vAlign w:val="%s"/>' % c["valign"])
                out.append('<w:tc><w:tcPr>%s</w:tcPr>' % "".join(cp))
                blocks = c.get("blocks") or [para()]
                self.blocks(part, blocks, out)
                if blocks and blocks[-1].get("table"):
                    out.append('<w:p/>')
                out.append('</w:tc>')
            out.append('</w:tr>')
        out.append('</w:tbl>')

    def sect_xml(self, part, s):
        out = ['<w:sectPr>']
        for kind, store in (("header", s.get("headers", {})), ("footer", s.get("footers", {}))):
            for typ in ("default", "first", "even"):
                if typ in store:
                    rid = self.hf(part, kind, store[typ])
                    out.append('<w:%sReference w:type="%s" r:id="%s"/>' % (kind, typ, rid))
        if s.get("break") and s["break"] != "nextPage":
            out.append('<w:type w:val="%s"/>' % s["break"])
        w, h = s["w"], s["h"]
        out.append('<w:pgSz w:w="%d" w:h="%d"%s/>' % (w, h, ' w:orient="landscape"' if s.get("landscape") else ""))
        m = s["margins"]
        out.append('<w:pgMar w:top="%d" w:right="%d" w:bottom="%d" w:left="%d" w:header="%d" '
                   'w:footer="%d" w:gutter="%d"/>' % (m["top"], m["right"], m["bottom"], m["left"],
                                                      m.get("header", 720), m.get("footer", 720),
                                                      m.get("gutter", 0)))
        if s.get("pgborders"):
            out.append('<w:pgBorders w:offsetFrom="text">%s</w:pgBorders>' % "".join(
                _border(side, s["pgborders"][side]) for side in ("top", "left", "bottom", "right")
                if side in s["pgborders"]))
        if s.get("page_start"):
            out.append('<w:pgNumType w:start="%d"/>' % s["page_start"])
        if s.get("cols", 1) > 1:
            out.append('<w:cols w:num="%d" w:space="%d"/>' % (s["cols"], s.get("col_space", 720)))
        else:
            out.append('<w:cols w:space="720"/>')
        if s.get("title_pg"):
            out.append('<w:titlePg/>')
        out.append('<w:docGrid w:linePitch="360"/></w:sectPr>')
        return "".join(out)

    def hf(self, part, kind, blocks):
        if kind == "header":
            self.headers += 1
            name = "header%d.xml" % self.headers
        else:
            self.footers += 1
            name = "footer%d.xml" % self.footers
        sub = _Part(self, name)
        out = []
        self.blocks(sub, blocks or [para()], out)
        tag = "hdr" if kind == "header" else "ftr"
        self.files["word/" + name] = (HDR + '<w:%s %s>%s</w:%s>' % (tag, NSDECL, "".join(out), tag)).encode()
        if sub.rels:
            self.files["word/_rels/%s.rels" % name] = sub.rels_xml().encode()
        self.overrides.append(("/word/" + name, "application/vnd.openxmlformats-officedocument.wordprocessingml.%s+xml" % kind))
        return part.rel(kind, name)

    def notes_part(self, kind, notes):
        tag = "footnote" if kind == "footnotes" else "endnote"
        sub = _Part(self, kind + ".xml")
        out = [HDR, '<w:%ss %s>' % (tag, NSDECL),
               '<w:%s w:type="separator" w:id="-1"><w:p><w:pPr><w:spacing w:after="0" w:line="240" '
               'w:lineRule="auto"/></w:pPr><w:r><w:separator/></w:r></w:p></w:%s>' % (tag, tag),
               '<w:%s w:type="continuationSeparator" w:id="0"><w:p><w:pPr><w:spacing w:after="0" '
               'w:line="240" w:lineRule="auto"/></w:pPr><w:r><w:continuationSeparator/></w:r></w:p></w:%s>' % (tag, tag)]
        st = "FootnoteText" if tag == "footnote" else "EndnoteText"
        ref = "FootnoteReference" if tag == "footnote" else "EndnoteReference"
        i = 0
        while i < len(notes):   # notes may hold notes of their own
            blocks = notes[i]
            i += 1
            body = []
            blocks = [dict(b) for b in (blocks or [para()])]
            if blocks and not blocks[0].get("table"):
                b0 = blocks[0]
                b0["style"] = b0.get("style") or st
                b0["runs"] = [{"t": "_ref"}] + list(b0.get("runs", []))
            for b in blocks:
                if b.get("table"):
                    self.table(sub, b, body)
                    continue
                inner = []
                runs = b.get("runs", [])
                if runs and runs[0].get("t") == "_ref":
                    inner.append('<w:r><w:rPr><w:rStyle w:val="%s"/></w:rPr><w:%sRef/></w:r>' % (ref, tag))
                    inner.append('<w:r><w:t xml:space="preserve"> </w:t></w:r>')
                    runs = runs[1:]
                self.runs(sub, runs, inner)
                body.append('<w:p>%s%s</w:p>' % (ppr_xml(b.get("ppr", {}), b.get("style") or st), "".join(inner)))
            out.append('<w:%s w:id="%d">%s</w:%s>' % (tag, i, "".join(body), tag))
        out.append('</w:%ss>' % tag)
        self.files["word/%s.xml" % kind] = "".join(out).encode()
        if sub.rels:
            self.files["word/_rels/%s.xml.rels" % kind] = sub.rels_xml().encode()
        self.overrides.append(("/word/%s.xml" % kind, "application/vnd.openxmlformats-officedocument.wordprocessingml.%s+xml" % kind))

    def comments_part(self):
        sub = _Part(self, "comments.xml")
        out = [HDR, '<w:comments %s>' % NSDECL]
        for c in self.doc.comments:
            body = []
            blocks = c.get("blocks") or [para()]
            for j, b in enumerate(blocks):
                inner = []
                if j == 0:
                    inner.append('<w:r><w:rPr><w:rStyle w:val="CommentReference"/></w:rPr><w:annotationRef/></w:r>')
                self.runs(sub, b.get("runs", []), inner)
                body.append('<w:p>%s%s</w:p>' % (ppr_xml(b.get("ppr", {}), "CommentText"), "".join(inner)))
            date = c.get("date") or ""
            out.append('<w:comment w:id="%d" w:author="%s"%s w:initials="%s">%s</w:comment>' % (
                c["id"], esc(c.get("author") or "Author"), ' w:date="%s"' % esc(date) if date else "",
                esc(c.get("initials") or _initials(c.get("author") or "")), "".join(body)))
        out.append('</w:comments>')
        self.files["word/comments.xml"] = "".join(out).encode()
        if sub.rels:
            self.files["word/_rels/comments.xml.rels"] = sub.rels_xml().encode()
        self.overrides.append(("/word/comments.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"))

    # ---- package parts
    def styles_xml(self):
        d = self.doc
        out = [HDR, '<w:styles %s>' % NSDECL]
        out.append('<w:docDefaults><w:rPrDefault>%s</w:rPrDefault><w:pPrDefault>%s</w:pPrDefault></w:docDefaults>' % (
            rpr_xml(d.defaults.get("rpr", {})) or "<w:rPr/>", ppr_xml(d.defaults.get("ppr", {})) or "<w:pPr/>"))
        have = {s["id"] for s in d.styles}
        need = [
            ("Normal", "Normal", "paragraph", None, {}, {}, True),
            ("DefaultParagraphFont", "Default Paragraph Font", "character", None, {}, {}, True),
            ("TableNormal", "Normal Table", "table", None, {}, {}, True),
            ("NoList", "No List", "numbering", None, {}, {}, True),
            ("Hyperlink", "Hyperlink", "character", "DefaultParagraphFont", {}, {"color": "0563C1", "u": "single"}, False),
            ("FootnoteText", "footnote text", "paragraph", "Normal", {"sa": 0, "line": 240}, {"sz": 20}, False),
            ("FootnoteReference", "footnote reference", "character", "DefaultParagraphFont", {}, {"vert": "superscript"}, False),
            ("EndnoteText", "endnote text", "paragraph", "Normal", {"sa": 0, "line": 240}, {"sz": 20}, False),
            ("EndnoteReference", "endnote reference", "character", "DefaultParagraphFont", {}, {"vert": "superscript"}, False),
            ("CommentText", "annotation text", "paragraph", "Normal", {"line": 240}, {"sz": 20}, False),
            ("CommentReference", "annotation reference", "character", "DefaultParagraphFont", {}, {"sz": 16}, False),
            ("Header", "header", "paragraph", "Normal", {"sa": 0, "line": 240, "tabs": [(4680, "center", None), (9360, "right", None)]}, {}, False),
            ("Footer", "footer", "paragraph", "Normal", {"sa": 0, "line": 240, "tabs": [(4680, "center", None), (9360, "right", None)]}, {}, False),
            ("ListParagraph", "List Paragraph", "paragraph", "Normal", {"ind_l": 720, "contextual": True}, {}, False),
            ("TableGrid", "Table Grid", "table", "TableNormal", {}, {}, False),
        ]
        for sid, name, kind, based, ppr, rpr, default in need:
            if sid not in have:
                s = {"id": sid, "name": name, "type": kind, "based": based, "ppr": ppr, "rpr": rpr,
                     "default": default}
                out.append(self.style_xml(s))
        for s in d.styles:
            out.append(self.style_xml(s))
        out.append('</w:styles>')
        return "".join(out)

    def style_xml(self, s):
        sid = s["id"]
        name = LOWER.get(sid, s.get("name") or sid)
        kind = s.get("type", "paragraph")
        x = ['<w:style w:type="%s"%s%s w:styleId="%s"><w:name w:val="%s"/>' % (
            kind, ' w:default="1"' if s.get("default") else "",
            ' w:customStyle="1"' if s.get("custom") else "", esc(sid), esc(name))]
        if s.get("based") and s["based"] != sid:
            x.append('<w:basedOn w:val="%s"/>' % esc(s["based"]))
        if s.get("next"):
            x.append('<w:next w:val="%s"/>' % esc(s["next"]))
        if kind == "table" and sid == "TableNormal":
            x.append('<w:uiPriority w:val="99"/><w:semiHidden/><w:unhideWhenUsed/><w:tblPr><w:tblInd w:w="0" w:type="dxa"/>'
                     '<w:tblCellMar><w:top w:w="0" w:type="dxa"/><w:left w:w="108" w:type="dxa"/>'
                     '<w:bottom w:w="0" w:type="dxa"/><w:right w:w="108" w:type="dxa"/></w:tblCellMar></w:tblPr>')
        elif kind == "table" and sid == "TableGrid":
            x.append('<w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/></w:pPr><w:tblPr><w:tblBorders>%s</w:tblBorders></w:tblPr>' % "".join(
                '<w:%s w:val="single" w:sz="4" w:space="0" w:color="auto"/>' % e
                for e in ("top", "left", "bottom", "right", "insideH", "insideV")))
        else:
            if kind != "numbering":
                x.append('<w:qFormat/>' if sid in ("Normal", "Title", "Subtitle", "Quote") or sid.startswith("Heading") else "")
            if kind == "paragraph":
                x.append(ppr_xml(s.get("ppr", {})))
            if kind in ("paragraph", "character"):
                x.append(rpr_xml(s.get("rpr", {})))
        x.append('</w:style>')
        return "".join(x)

    def numbering_xml(self):
        d = self.doc
        out = [HDR, '<w:numbering %s>' % NSDECL]
        for ai, levels in enumerate(d.lists):
            out.append('<w:abstractNum w:abstractNumId="%d"><w:multiLevelType w:val="%s"/>' % (
                ai, "hybridMultilevel" if len(levels) > 1 else "singleLevel"))
            for li, lv in enumerate(levels[:9]):
                fmt = lv.get("fmt", "decimal")
                text = lv.get("text")
                if text is None:
                    text = lv.get("bullet", "•") if fmt == "bullet" else "%%%d." % (li + 1)
                ind = lv.get("ind", 720 * (li + 1))
                hang = lv.get("hang", 360)
                out.append('<w:lvl w:ilvl="%d"><w:start w:val="%d"/><w:numFmt w:val="%s"/>'
                           '<w:lvlText w:val="%s"/><w:lvlJc w:val="%s"/>'
                           '<w:pPr><w:ind w:left="%d" w:hanging="%d"/></w:pPr>%s</w:lvl>' % (
                               li, lv.get("start", 1), fmt, esc(text), lv.get("jc", "left"), ind, hang,
                               rpr_xml(lv.get("rpr") or ({"font": lv["font"]} if lv.get("font") else {}))))
            out.append('</w:abstractNum>')
        for ni, (ai, restart) in enumerate(d.nums):
            if restart:
                out.append('<w:num w:numId="%d"><w:abstractNumId w:val="%d"/>%s</w:num>' % (
                    ni + 1, ai, "".join('<w:lvlOverride w:ilvl="%d"><w:startOverride w:val="%d"/></w:lvlOverride>'
                                        % (li, lv.get("start", 1)) for li, lv in enumerate(d.lists[ai][:9]))))
            else:
                out.append('<w:num w:numId="%d"><w:abstractNumId w:val="%d"/></w:num>' % (ni + 1, ai))
        out.append('</w:numbering>')
        return "".join(out)

    def build(self):
        d = self.doc
        body = _Part(self, "document.xml")
        out = [HDR, '<w:document %s><w:body>' % NSDECL]
        secs = d.sections or [section()]
        for i, s in enumerate(secs):
            sx = self.sect_xml(body, s)
            if i == len(secs) - 1:
                self.blocks(body, s["blocks"] or [para()], out)
                out.append(sx)
            else:
                self.blocks(body, s["blocks"], out, last_sect=sx)
        out.append('</w:body></w:document>')
        self.files["word/document.xml"] = "".join(out).encode()
        if self.footnotes or self.endnotes:
            self.notes_part("footnotes", self.footnotes)
            self.notes_part("endnotes", self.endnotes)
        if d.comments:
            self.comments_part()
        base = [("rIdStyles", "styles", "styles.xml"), ("rIdSettings", "settings", "settings.xml"),
                ("rIdFonts", "fontTable", "fontTable.xml")]
        self.files["word/styles.xml"] = self.styles_xml().encode()
        self.files["word/settings.xml"] = self.settings_xml().encode()
        self.files["word/fontTable.xml"] = self.fonts_xml().encode()
        if d.lists:
            self.files["word/numbering.xml"] = self.numbering_xml().encode()
            base.append(("rIdNumbering", "numbering", "numbering.xml"))
            self.overrides.append(("/word/numbering.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"))
        if self.footnotes or self.endnotes:
            base.append(("rIdFootnotes", "footnotes", "footnotes.xml"))
            base.append(("rIdEndnotes", "endnotes", "endnotes.xml"))
        if d.comments:
            base.append(("rIdComments", "comments", "comments.xml"))
        self.files["word/_rels/document.xml.rels"] = body.rels_xml(base).encode()
        self.files["docProps/core.xml"] = self.core_xml().encode()
        self.files["docProps/app.xml"] = (HDR + '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"><Application>Folio Writer</Application></Properties>').encode()
        self.files["_rels/.rels"] = (HDR + (
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>'
            '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
            '</Relationships>')).encode()
        self.files["[Content_Types].xml"] = self.types_xml().encode()
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("[Content_Types].xml", self.files.pop("[Content_Types].xml"))
            for name, data in self.files.items():
                z.writestr(name, data)
        return buf.getvalue()

    def settings_xml(self):
        extra = ""
        if self.doc.sections and any(s["headers"].get("even") or s["footers"].get("even") for s in self.doc.sections):
            extra += '<w:evenAndOddHeaders/>'
        return HDR + ('<w:settings %s><w:zoom w:percent="100"/>%s<w:defaultTabStop w:val="%d"/>'
                      '<w:characterSpacingControl w:val="doNotCompress"/>'
                      '<w:compat><w:compatSetting w:name="compatibilityMode" w:uri="http://schemas.microsoft.com/office/word" w:val="15"/></w:compat>'
                      '</w:settings>' % (NSDECL, extra, self.doc.tab_stop or 720))

    def fonts_xml(self):
        fonts = set()
        for s in self.doc.styles:
            if s.get("rpr", {}).get("font"):
                fonts.add(s["rpr"]["font"])
        if self.doc.defaults.get("rpr", {}).get("font"):
            fonts.add(self.doc.defaults["rpr"]["font"])
        return HDR + '<w:fonts %s>%s</w:fonts>' % (NSDECL, "".join('<w:font w:name="%s"/>' % esc(f) for f in sorted(fonts)))

    def core_xml(self):
        m = self.doc.meta
        now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        parts = []
        for k, tag in (("title", "dc:title"), ("subject", "dc:subject"), ("creator", "dc:creator"),
                       ("keywords", "cp:keywords"), ("description", "dc:description")):
            if m.get(k):
                parts.append("<%s>%s</%s>" % (tag, esc(m[k]), tag))
        created = m.get("created") or now
        return HDR + ('<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
                      'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
                      'xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
                      '%s<dcterms:created xsi:type="dcterms:W3CDTF">%s</dcterms:created>'
                      '<dcterms:modified xsi:type="dcterms:W3CDTF">%s</dcterms:modified></cp:coreProperties>'
                      % ("".join(parts), esc(created), esc(m.get("modified") or now)))

    def types_xml(self):
        mt = {"png": "image/png", "jpg": "image/jpeg", "gif": "image/gif", "bmp": "image/bmp",
              "tif": "image/tiff", "tiff": "image/tiff", "svg": "image/svg+xml", "emf": "image/x-emf",
              "wmf": "image/x-wmf"}
        out = [HDR, '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
               '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
               '<Default Extension="xml" ContentType="application/xml"/>']
        for ext in sorted(self.media_types):
            out.append('<Default Extension="%s" ContentType="%s"/>' % (ext, mt.get(ext, "application/octet-stream")))
        base = [("/word/document.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"),
                ("/word/styles.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"),
                ("/word/settings.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"),
                ("/word/fontTable.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.fontTable+xml"),
                ("/docProps/core.xml", "application/vnd.openxmlformats-package.core-properties+xml"),
                ("/docProps/app.xml", "application/vnd.openxmlformats-officedocument.extended-properties+xml")]
        for name, ct in base + self.overrides:
            out.append('<Override PartName="%s" ContentType="%s"/>' % (name, ct))
        out.append('</Types>')
        return "".join(out)


def _clean(s):
    """Characters XML 1.0 can't hold are dropped."""
    return "".join(c for c in s if c in "\t\n\r" or ord(c) >= 0x20 and not 0xD800 <= ord(c) <= 0xDFFF
                   and c not in "￾￿")


def _initials(name):
    return "".join(w[0] for w in name.split() if w)[:4].upper()


def to_docx(doc):
    """The .docx package for a Doc, as bytes."""
    return _Writer(doc).build()
