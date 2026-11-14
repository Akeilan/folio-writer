#!/usr/bin/env python3
"""Build the engine's test fixtures (core/tests/data). They used to be files from an outside
corpus that is not part of this repository, so core/tests/edit.rs failed on any machine without
it; now `cargo test` has everything it needs here (W5-22)."""
import os
import sys
from docx import Document
from docx.shared import Pt, Inches
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "core", "tests", "data")
os.makedirs(OUT, exist_ok=True)
L = ("The quick brown fox jumps over the lazy dog while the sun sets behind the quiet hills and "
     "the river runs on past the old stone bridge. ")

d = Document()
s = d.sections[0]
s.header.paragraphs[0].text = "Sample header"
s.footer.paragraphs[0].text = "Sample footer"
d.add_paragraph(L * 2)
d.add_paragraph(L)
d.add_paragraph("A third paragraph, shorter than the others.")
d.add_heading("A heading", 1)
for i in range(3):
    d.add_paragraph("List item %d" % i, style="List Bullet")
t = d.add_table(rows=2, cols=2)
t.style = "Table Grid"
for r in range(2):
    for c in range(2):
        t.cell(r, c).text = "r%dc%d" % (r, c)
p = d.add_paragraph("Mixed ")
p.add_run("bold").bold = True
p.add_run(" and ")
p.add_run("italic").italic = True
p.add_run(" and 14pt").font.size = Pt(14)
for i in range(60):
    d.add_paragraph(L * 2)
d.save(os.path.join(OUT, "sample.docx"))

# several pages, a title page with no header of its own, page numbers in the footer, and a
# table of a shape the layout has to cope with
d = Document()
s = d.sections[0]
s.different_first_page_header_footer = True
s.header.paragraphs[0].text = "Running header"
foot = s.footer.paragraphs[0]
foot.text = ""
run = foot.add_run()
for instr in ("PAGE",):
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), " %s " % instr)
    inner = OxmlElement("w:r")
    t_ = OxmlElement("w:t")
    t_.text = "1"
    inner.append(t_)
    fld.append(inner)
    foot._p.append(fld)
d.add_paragraph("Title page", style="Title")
d.add_page_break()
d.add_paragraph("Before the table.")
t = d.add_table(rows=3, cols=3)
t.style = "Table Grid"
t.cell(0, 0).merge(t.cell(0, 2)).text = "merged across"
t.cell(1, 1).text = "middle"
t.cell(2, 0).width = Inches(4)
d.add_paragraph("After the table.")
for i in range(40):
    d.add_paragraph(L * 2)
d.save(os.path.join(OUT, "Bug51170.docx"))
print("wrote", sorted(os.listdir(OUT)))
