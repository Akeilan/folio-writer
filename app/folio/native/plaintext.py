"""Opening a plain text file.

Two things the obvious way gets wrong (W5-08, W5-09):

* the file need not be UTF-8. A file written by an older editor is usually in the computer's
  8-bit encoding, and a file from Windows may be UTF-16; reading either as UTF-8 fills the page
  with replacement marks or with nulls. `read` works out the encoding from the byte-order mark
  where there is one, then tries UTF-8, then the usual 8-bit encodings, which always decode.
* typing the text in character by character is how it used to be loaded, and a 2.4 MB file took
  the best part of a minute. `editor_for` writes the paragraphs straight into a copy of the
  template instead and opens that, which is the same work the engine does for any .docx.
"""
import io
import re
import zipfile

BOMS = [(b"\xef\xbb\xbf", "utf-8-sig"), (b"\xff\xfe\x00\x00", "utf-32"), (b"\x00\x00\xfe\xff", "utf-32"),
        (b"\xff\xfe", "utf-16"), (b"\xfe\xff", "utf-16")]
# after UTF-8: the two 8-bit encodings a text file on a desktop is most likely to be in. Both
# decode any byte, so one of them always succeeds and the file is never shown as rubbish.
FALLBACKS = ["cp1252", "latin-1"]


def encoding_of(data):
    """The encoding to read these bytes as."""
    for bom, enc in BOMS:
        if data.startswith(bom):
            return enc
    # UTF-16 without a mark: ASCII text comes out as alternating nulls
    head = data[:4096]
    if head and head.count(b"\x00") > len(head) // 4:
        return "utf-16-le" if head[1:2] == b"\x00" else "utf-16-be"
    for enc in ["utf-8"] + FALLBACKS:
        try:
            data.decode(enc)
            return enc
        except (UnicodeDecodeError, LookupError):
            continue
    return "latin-1"


def read(path):
    """A text file's lines, however it was encoded."""
    with open(path, "rb") as fh:
        data = fh.read()
    enc = encoding_of(data)
    try:
        text = data.decode(enc, errors="replace")
    except LookupError:
        text = data.decode("latin-1", errors="replace")
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace("\x00", ""))


# characters XML cannot carry at all
_BAD = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f]")


def paragraphs_xml(text):
    """The text as Word paragraphs."""
    out = []
    for line in text.rstrip("\n").split("\n"):
        line = _BAD.sub("", line)
        if not line:
            out.append("<w:p/>")
            continue
        parts = line.split("\t")
        runs = []
        for i, part in enumerate(parts):
            if i:
                runs.append("<w:r><w:tab/></w:r>")
            if part:
                runs.append('<w:r><w:t xml:space="preserve">%s</w:t></w:r>' % _esc(part))
        out.append("<w:p>%s</w:p>" % "".join(runs))
    return "".join(out) or "<w:p/>"


def editor_for(core, template, text):
    """An editor holding this text, built from the template without typing it in."""
    if not template:
        ed = core.Editor.open(template)
        if text:
            ed.type_text(text.rstrip("\n"))
        return ed
    with open(template, "rb") as fh:
        raw = fh.read()
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        parts = {n: z.read(n) for n in z.namelist()}
    doc = parts.get("word/document.xml", b"").decode("utf-8", "replace")
    body = doc.find("<w:body")
    end = doc.find("</w:body>")
    if body < 0 or end < 0:
        ed = core.Editor.open(template)
        if text:
            ed.type_text(text.rstrip("\n"))
        return ed
    open_end = doc.find(">", body) + 1
    inner = doc[open_end:end]
    sect = ""
    at = inner.rfind("<w:sectPr")
    if at >= 0:
        sect = inner[at:]
    parts["word/document.xml"] = (doc[:open_end] + paragraphs_xml(text) + sect + doc[end:]).encode("utf-8")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for n, b in parts.items():
            z.writestr(n, b)
    return core.Editor.from_bytes(buf.getvalue())
