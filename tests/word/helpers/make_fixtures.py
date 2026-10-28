# Builds the parity suite's sample files (/tmp/wfid, /tmp/wfid2) with Folio's engine.
# Run inside the build root: PYTHONPATH=/tmp/fw/app python3 make_fixtures.py
import os
import sys
import zlib
import struct

sys.path.insert(0, "/tmp/fw/app")
import folio_core as core  # noqa: E402

BLANK = "/tmp/fw/share/templates/Normal-Letter.docx"
for d in ("/tmp/wfid", "/tmp/wfid2", "/tmp/dc"):
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
ed.type_text("Removed by Bob.")
p, off = ed.caret_pos()
ed.select_nodes(p, 0, p, 0)
ed.set_track_changes(True)
ed.type_text("Inserted by Alice. ")
ed.set_author("Bob")
p, off = ed.caret_pos()
n = len(ed.para_text_of(p))
ed.select_nodes(p, n - 15, p, n)
ed.delete(True, False)
ed.set_track_changes(False)
ed.set_author("Alice")
ed.move_caret("doc_end", False)
ed.type_text("\n")
for k in range(3):
    tried("control", ed.insert_content_control, "<w:sdtPr><w:alias w:val=\"Field %d\"/></w:sdtPr>" % k, "Click here %d" % k)
    ed.move_caret("doc_end", False)
    ed.type_text("\n")
tried("picture", ed.insert_picture, "/tmp/wfid/pic.png")
pics = [o for o in ed.objects_list() if o[2] == "Picture"]
if pics:
    ed.select_object_node(pics[0][0])
    tried("float", ed.object_set_wrap, "square")
    ed.deselect_object()
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

# ---- fid2.docx: fid.docx plus a drop cap, line numbers, a page border, first / even
# headers and a two-column section
import shutil
ed = core.Editor.open("/tmp/wfid/fid.docx")
ed.move_caret("doc_start", False)
ed.move_caret("doc_start", False)
tried("drop cap", ed.set_drop_cap, "drop", 3, 0, None)
tried("line numbers", ed.set_line_numbers, "continuous", 1, 0, 0, True)
tried("page border", ed.set_page_borders, None,
      '<w:pgBorders xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:offsetFrom="page">'
      '<w:left w:val="single" w:sz="12" w:space="24" w:color="2E6B3F"/></w:pgBorders>')
tried("title page", ed.section_flag, 0, "w:titlePg", True)
tried("odd/even", ed.set_setting, "evenAndOddHeaders", True)
for which in (0, 1, 2):
    tried("make header", ed.ensure_header_footer_kind, 0, False, which)
for pg, txt in ((0, "First page header"), (1, "Even page header"), (2, "Odd page header")):
    tried("hf", ed.edit_header_footer, pg, False)
    ed.type_text(txt)
tried("body", ed.edit_header_footer, None, False)
ed.move_caret("doc_end", False)
tried("section", ed.insert_break, "continuous")
ed.type_text("Two columns of text. " * 20)
sec = ed.current_section()
tried("columns", ed.section_attr, sec, "w:cols", "w:num", "2", "Columns")
ed.save("/tmp/wfid2/fid2.docx")
print("fid2.docx", ed.page_count(), "pages, headers kinds", [ed.page_hf_kind(i) for i in range(ed.page_count())])
open("/tmp/wfid2/people.csv", "w").write("First Name,Last Name,City\nAnn,Smith,Delft\nBen,Jones,Leeds\n")
print("fixtures done")

# ---- big.docx: 100 chapters, one a page (the speed scenarios)
ed = core.Editor.open(BLANK)
body = ("The quick brown fox jumps over the lazy dog while the report goes on about nothing "
        "in particular, line after line, so that the page fills up with ordinary text. ") * 4
for i in range(1, 101):
    if i > 1:
        ed.insert_break("page")
    ed.type_text("Chapter %d\n" % i)
    for _k in range(3):
        ed.type_text(body + "\n")
ed.save("/tmp/wfid/big.docx")
print("big.docx", ed.page_count(), "pages")

# ---- /tmp/dc: a 4:3 picture for the picture-layout scenarios
png("/tmp/dc/pic.png", 160, 120, (60, 120, 200))
