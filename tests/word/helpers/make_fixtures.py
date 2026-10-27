# Builds the parity suite's sample files (/tmp/wfid, /tmp/wfid2) with Folio's engine.
# Run inside the build root: PYTHONPATH=/tmp/fw/app python3 make_fixtures.py
import os
import sys
import zlib
import struct

sys.path.insert(0, "/tmp/fw/app")
import folio_core as core  # noqa: E402

BLANK = "/tmp/fw/share/templates/Normal-Letter.docx"
for d in ("/tmp/wfid", "/tmp/wfid2"):
    os.makedirs(d, exist_ok=True)


def png(path, w=120, h=80, rgb=(200, 60, 40)):
    raw = b"".join(b"\x00" + bytes(rgb) * w for _ in range(h))
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    data = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + \
        chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")
    open(path, "wb").write(data)


def tried(name, fn, *a):
    try:
        return fn(*a)
    except Exception as e:
        print("fixture %s: %s" % (name, e))


png("/tmp/wfid/pic.png")
png("/tmp/wfid2/pic.png")

# ---- fid.docx: four pages with notes, comments, changes, controls, objects
ed = core.Editor.open(BLANK)
ed.set_author("Alice")
ed.type_text("Fidelity sample\n")
ed.type_text("Dear reader, this paragraph has a footnote")
tried("footnote", ed.insert_note, False)
ed.type_text("footnote text")
tried("leave note", ed.edit_notes, None)
ed.move_caret("doc_end", False)
ed.type_text(" and an endnote")
tried("endnote", ed.insert_note, True)
ed.type_text("endnote text")
tried("leave note", ed.edit_notes, None)
ed.move_caret("doc_end", False)
ed.type_text("\nA bookmarked word: ")
ed.type_text("Target")
p, off = ed.caret_pos()
ed.select_nodes(p, off - 6, p, off)
tried("bookmark", ed.add_bookmark, "Target1")
ed.move_caret("doc_end", False)
ed.type_text("\nThis sentence has a comment.")
p, off = ed.caret_pos()
ed.select_nodes(p, 0, p, 4)
tried("comment", ed.insert_comment, "Reviewer note", "Reviewer")
ed.move_caret("doc_end", False)
ed.type_text("\n")
ed.set_track_changes(True)
ed.type_text("Inserted by Alice. ")
ed.set_author("Bob")
ed.type_text("Removed by Bob.")
p, off = ed.caret_pos()
ed.set_track_changes(False)
ed.set_track_changes(True)
ed.select_nodes(p, off - 15, p, off)
ed.delete(True, False)
ed.set_track_changes(False)
ed.move_caret("doc_end", False)
ed.type_text("\n")
for k in range(3):
    tried("control", ed.insert_content_control, "<w:sdtPr><w:alias w:val=\"Field %d\"/></w:sdtPr>" % k, "Click here %d" % k)
    ed.move_caret("doc_end", False)
    ed.type_text("\n")
tried("picture", ed.insert_picture, "/tmp/wfid/pic.png")
ed.move_caret("doc_end", False)
for pg in range(3):
    tried("break", ed.insert_break, "page")
    ed.type_text("Page %d text\n" % (pg + 2))
tried("textbox", ed.insert_shape, "rect", 1, 300, 200, 150, 60, "Text Box 1", False)
ed.save("/tmp/wfid/fid.docx")
print("fid.docx", ed.page_count(), "pages")

# ---- math.docx
ed = core.Editor.open(BLANK)
ed.type_text("Equations\n")
M = ('<m:oMath xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math">'
     '<m:r><m:t>a</m:t></m:r><m:r><m:t>=</m:t></m:r><m:f><m:num><m:r><m:t>b</m:t></m:r></m:num>'
     '<m:den><m:r><m:t>c</m:t></m:r></m:den></m:f></m:oMath>')
tried("math", ed.insert_math, M, True)
ed.move_caret("doc_end", False)
ed.type_text("\nInline ")
tried("math2", ed.insert_math, M, False)
ed.save("/tmp/wfid/math.docx")

# ---- fid2.docx and the recipients
ed = core.Editor.open(BLANK)
ed.type_text("Second sample\n")
ed.save("/tmp/wfid2/fid2.docx")
open("/tmp/wfid2/people.csv", "w").write("First Name,Last Name,City\nAnn,Smith,Delft\nBen,Jones,Leeds\n")
print("fixtures done")
