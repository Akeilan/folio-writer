# Page findings (running notes)
1. Undo leaves parts behind in the file: after undoing a header/footer/watermark/comment/footnote/bullets, the saved .docx still holds the part (header21.xml etc.); undoing Margins>Mirrored leaves mirrorMargins set. [p1b]
2. Save as .odt/.rtf/.doc silently drops: shapes, tracked insertions (become plain text), content controls (odt not warned), highlight (odt). Compatibility checker warns of none of these. [p3]
3. .doc round trip: 3x3 table comes back with 12 cells, extra blank paragraphs. [p3]
4. HTML reader ignores <b>, <i>, <sub>, <s>, highlight, footnotes, header/footer when opening .html it wrote itself. [p3]
5. Command walk never visits Table Design, Table Layout, Header & Footer, Equation, Chart Design, SmartArt Design tabs (excluded, no setup). Coverage gap.
6. engine toggle("bold") (unknown name) writes an invalid <bold/> element into the docx — macros can corrupt files. [p3 first run]
7. Convert Text to Table: OK in the dialog raises AttributeError setString (dlg_table.py:102 uses the old UNO model). Feature dead. [p2]
8. RTL scripts: Arabic drawn unshaped and left-to-right; Hebrew drawn in reverse order. No bidi. [p8 screenshot]
9. Emoji: monochrome; skin-tone modifier drawn as a separate box. [p8]
10. Reading .doc: headers/footers of later sections and pages lost (sections.doc). Reading .odt: every page gets the first-page header, others lost; column break lost (breaks.odt 3 pages vs 4); chart object dropped (61745.odt). Reading .rtf: A5 section size lost, landscape header lost, 5 pages vs 6. [p7,p9]
11. OK: corpus of 13 docx + LO-written docx/doc/odt/rtf (65 files) all open, no errors; page counts match LibreOffice on all docx (92-page doc included); words all present.
12. OK: equations tab works at user level (my p4 setup was wrong).
13. Baseline suites on rebuilt machine: native 46/48 scripts clean, word 55/57; the 4 failures are the machine (xclip missing then, DejaVu UI font making ribbon 101px). Need re-run.
