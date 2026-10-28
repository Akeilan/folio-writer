#!/usr/bin/env python3
"""Build tests/data/import/sample.{docx,odt,doc}: a document with the features the
OpenDocument and Word 97-2003 readers must keep. The .odt and .doc are written by
LibreOffice (run once on a developer machine) so the tests read files as another
program writes them."""
import os
import subprocess
import sys
import zlib
import struct

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "app"))
from folio.native import docxbuild as B  # noqa: E402


def png(w, h, rgb):
    raw = b"".join(b"\x00" + bytes(rgb) * w for _ in range(h))
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) +
            chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


d = B.Doc()
d.defaults["rpr"] = {"font": "Liberation Serif", "sz": 24}
d.add_style("Normal", "Normal", default=True, ppr={"sa": 120})
d.add_style("Heading1", "Heading 1", based="Normal", nxt="Normal", ppr={"sb": 240, "sa": 120, "keep_next": True, "outline": 0},
            rpr={"font": "Liberation Sans", "sz": 32, "b": True, "color": "2E6B3F"})
d.add_style("Heading2", "Heading 2", based="Normal", nxt="Normal", ppr={"sb": 200, "sa": 80, "outline": 1},
            rpr={"font": "Liberation Sans", "sz": 28, "b": True, "i": True})
d.lists.append([{"fmt": "bullet", "text": "•", "ind": 720 * (i + 1), "hang": 360} for i in range(9)])
d.lists.append([{"fmt": "decimal", "text": "%%%d." % (i + 1), "ind": 720 * (i + 1), "hang": 360} for i in range(9)])
d.nums += [(0, False), (1, False)]
s = B.section()
s["headers"]["default"] = [B.para("Folio header", "Header")]
s["footers"]["default"] = [{"style": "Footer", "ppr": {"align": "center"}, "rpr": {},
                            "runs": [{"t": "text", "text": "Page ", "rpr": {}}, {"t": "field", "instr": "PAGE", "result": "1"}]}]
bl = s["blocks"]
bl.append(B.para("Import test", "Heading1"))
bl.append({"style": "Normal", "ppr": {}, "rpr": {}, "runs": [
    {"t": "text", "text": "Plain, ", "rpr": {}}, {"t": "text", "text": "bold", "rpr": {"b": True}},
    {"t": "text", "text": ", ", "rpr": {}}, {"t": "text", "text": "italic", "rpr": {"i": True}},
    {"t": "text", "text": " and ", "rpr": {}}, {"t": "text", "text": "red underlined", "rpr": {"color": "C00000", "u": "single"}},
    {"t": "text", "text": " text with a note", "rpr": {}},
    {"t": "note", "kind": "footnote", "blocks": [B.para("The footnote text.")], "rpr": {}},
    {"t": "text", "text": ".", "rpr": {}}]})
bl.append({"style": "Normal", "ppr": {"align": "center"}, "rpr": {}, "runs": [
    {"t": "text", "text": "Centred with a comment", "rpr": {}}, {"t": "cstart", "id": 0}, {"t": "cend", "id": 0}]})
d.comments.append({"id": 0, "author": "Test Author", "initials": "TA", "date": "2026-10-28T10:00:00Z",
                   "blocks": [B.para("A comment.")]})
bl.append(B.para("Lists", "Heading2"))
for t, n, lv in (("First bullet", 0, 0), ("Second bullet", 0, 0), ("Nested bullet", 0, 1),
                 ("First number", 1, 0), ("Second number", 1, 0)):
    bl.append({"style": "Normal", "ppr": {"num": (n, lv)}, "rpr": {}, "runs": [{"t": "text", "text": t, "rpr": {}}]})
bl.append(B.para("A table", "Heading2"))
bl.append({"table": True, "cols": [3000, 3000], "rows": [
    {"cells": [{"blocks": [B.para("A1", rpr={"b": True})], "shd": "D9E2D3"}, {"blocks": [B.para("B1", rpr={"b": True})], "shd": "D9E2D3"}], "header": True},
    {"cells": [{"blocks": [B.para("A2")]}, {"blocks": [B.para("B2")]}]},
    {"cells": [{"blocks": [B.para("Merged across")], "span": 2}]}]})
bl.append({"style": "Normal", "ppr": {}, "rpr": {}, "runs": [
    {"t": "text", "text": "A picture: ", "rpr": {}},
    {"t": "image", "data": png(40, 20, (46, 107, 63)), "ext": "png", "cx": 40 * 9525 * 2, "cy": 20 * 9525 * 2}]})
bl.append({"style": "Normal", "ppr": {"pbb": True}, "rpr": {}, "runs": [{"t": "text", "text": "Second page.", "rpr": {}}]})
d.sections.append(s)
d.meta["title"] = "Import test"
out = os.path.join(HERE, "..", "tests", "data", "import")
os.makedirs(out, exist_ok=True)
with open(os.path.join(out, "sample.docx"), "wb") as fh:
    fh.write(B.to_docx(d))
for fmt, filt in (("odt", "odt"), ("doc", "doc:MS Word 97")):
    subprocess.run(["soffice", "--headless", "--convert-to", filt, "--outdir", out,
                    os.path.join(out, "sample.docx")], check=True, capture_output=True)
print("written", out)
