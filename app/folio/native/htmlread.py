"""Reading a whole .html page as a document: the body through Folio's own HTML
reader (the one Paste uses), its pictures embedded as parts. Nothing is fetched
over the network; a picture is read from a data: URI or from a file beside the
page."""
import io
import os
import re
import zipfile

from . import htmlpaste, plaintext

MIME = {"png": "image/png", "jpg": "image/jpeg", "gif": "image/gif", "bmp": "image/bmp",
        "tiff": "image/tiff", "webp": "image/webp", "svg": "image/svg+xml"}
REL = ("http://schemas.openxmlformats.org/officeDocument/2006/relationships/image")


def parts_of(template):
    with open(template, "rb") as fh:
        raw = fh.read()
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        return {n: z.read(n) for n in z.namelist()}


def _style_ids(parts):
    s = parts.get("word/styles.xml", b"").decode("utf-8", "replace")
    return set(re.findall(r'w:styleId="([^"]+)"', s))


def _numbering(kinds):
    """A numbering part for the lists a page used: a bullet list and a numbered
    one, nine levels each, indented as Word indents them."""
    abs_defs, nums = [], []
    for which, num_id in (("bullet", htmlpaste.NUM_BULLET), ("number", htmlpaste.NUM_NUMBER)):
        if which not in kinds:
            continue
        aid = num_id
        lvls = []
        for l in range(9):
            if which == "bullet":
                fmt, txt, font = "bullet", ("\u2022", "o", "\u25aa")[l % 3], \
                    ("Symbol", "Courier New", "Wingdings")[l % 3]
                rpr = '<w:rPr><w:rFonts w:ascii="%s" w:hAnsi="%s" w:hint="default"/></w:rPr>' % (font, font)
            else:
                fmt, txt = ("decimal", "lowerLetter", "lowerRoman")[l % 3], "%%%d." % (l + 1)
                rpr = ""
            lvls.append('<w:lvl w:ilvl="%d"><w:start w:val="1"/><w:numFmt w:val="%s"/>'
                        '<w:lvlText w:val="%s"/><w:lvlJc w:val="left"/>'
                        '<w:pPr><w:ind w:left="%d" w:hanging="360"/></w:pPr>%s</w:lvl>'
                        % (l, fmt, txt, 720 + 720 * l, rpr))
        abs_defs.append('<w:abstractNum w:abstractNumId="%d"><w:multiLevelType w:val="hybridMultilevel"/>%s'
                        '</w:abstractNum>' % (aid, "".join(lvls)))
        nums.append('<w:num w:numId="%d"><w:abstractNumId w:val="%d"/></w:num>' % (num_id, aid))
    return abs_defs, nums


def _xml_attr(v):
    return (v or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def title_of(text):
    m = re.search(r"<title[^>]*>(.*?)</title>", text, re.S | re.I)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""


def read(path):
    """The page's text, whatever it is encoded in."""
    return plaintext.read(path)


def editor_for(core, template, path):
    """An editor holding the page at `path`, built on the blank template."""
    text = read(path)
    styles = _style_ids(parts_of(template))
    body, media, hrefs, lists = htmlpaste.to_document(
        text, styles, os.path.dirname(os.path.abspath(path)))
    if not body.strip():
        body = "<w:p/>"
    parts = parts_of(template)
    doc = parts.get("word/document.xml", b"").decode("utf-8", "replace")
    start, end = doc.find("<w:body"), doc.find("</w:body>")
    if start < 0 or end < 0:
        raise RuntimeError("the template has no body")
    open_end = doc.find(">", start) + 1
    inner = doc[open_end:end]
    at = inner.rfind("<w:sectPr")
    sect = inner[at:] if at >= 0 else ""
    parts["word/document.xml"] = (doc[:open_end] + body + sect + doc[end:]).encode("utf-8")
    if media or hrefs:
        rels_name = "word/_rels/document.xml.rels"
        rels = parts.get(rels_name, b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                                    b'<Relationships xmlns="http://schemas.openxmlformats.org/'
                                    b'package/2006/relationships"></Relationships>').decode("utf-8", "replace")
        add = []
        for i, href in enumerate(hrefs, 1):
            add.append('<Relationship Id="rIdHtmlLink%d" Type="%shyperlink" Target="%s" '
                       'TargetMode="External"/>'
                       % (i, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/",
                          _xml_attr(href)))
        for n, data, ext in media:
            name = "media/htmlimage%d.%s" % (n, ext)
            parts["word/" + name] = data
            add.append('<Relationship Id="rIdHtml%d" Type="%s" Target="%s"/>' % (n, REL, name))
        rels = rels.replace("</Relationships>", "".join(add) + "</Relationships>")
        parts[rels_name] = rels.encode("utf-8")
        # every picture's type must be declared
        ct_name = "[Content_Types].xml"
        ct = parts.get(ct_name, b"").decode("utf-8", "replace")
        for ext in sorted({e for _n, _d, e in media}):
            if 'Extension="%s"' % ext not in ct:
                ct = ct.replace("</Types>", '<Default Extension="%s" ContentType="%s"/></Types>'
                                % (ext, MIME.get(ext, "image/png")))
        parts[ct_name] = ct.encode("utf-8")
    if lists:
        abs_defs, nums = _numbering(lists)
        name = "word/numbering.xml"
        cur = parts.get(name, b"").decode("utf-8", "replace")
        if "<w:numbering" in cur:
            cur = cur.replace("</w:numbering>", "".join(abs_defs) + "".join(nums) + "</w:numbering>")
        else:
            cur = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<w:numbering xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                   + "".join(abs_defs) + "".join(nums) + "</w:numbering>")
        parts[name] = cur.encode("utf-8")
        rels_name = "word/_rels/document.xml.rels"
        rels = parts.get(rels_name, b"").decode("utf-8", "replace")
        if "numbering.xml" not in rels:
            rels = rels.replace("</Relationships>",
                                '<Relationship Id="rIdHtmlNum" Type="%snumbering" Target="numbering.xml"/>'
                                '</Relationships>'
                                % "http://schemas.openxmlformats.org/officeDocument/2006/relationships/")
            parts[rels_name] = rels.encode("utf-8")
        ct = parts.get("[Content_Types].xml", b"").decode("utf-8", "replace")
        if "numbering+xml" not in ct:
            ct = ct.replace("</Types>", '<Override PartName="/word/numbering.xml" ContentType='
                            '"application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>'
                            '</Types>')
            parts["[Content_Types].xml"] = ct.encode("utf-8")
        st = parts.get("word/styles.xml", b"").decode("utf-8", "replace")
        if 'w:styleId="ListParagraph"' not in st:
            st = st.replace("</w:styles>", '<w:style w:type="paragraph" w:styleId="ListParagraph">'
                            '<w:name w:val="List Paragraph"/><w:basedOn w:val="Normal"/>'
                            '<w:uiPriority w:val="34"/><w:qFormat/>'
                            '<w:pPr><w:ind w:left="720"/><w:contextualSpacing/></w:pPr>'
                            '</w:style></w:styles>')
            parts["word/styles.xml"] = st.encode("utf-8")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for n, b in parts.items():
            z.writestr(n, b)
    return core.Editor.from_bytes(buf.getvalue())
