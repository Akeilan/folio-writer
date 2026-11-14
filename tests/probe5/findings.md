# Page findings (running notes)
1. Undo leaves parts behind in the file: after undoing a header/footer/watermark/comment/footnote/bullets, the saved .docx still holds the part (header21.xml etc.); undoing Margins>Mirrored leaves mirrorMargins set. [p1b]
2. Save as .odt/.rtf/.doc silently drops: shapes, tracked insertions (become plain text), content controls (odt not warned), highlight (odt). Compatibility checker warns of none of these. [p3]
3. .doc round trip: 3x3 table comes back with 12 cells, extra blank paragraphs. [p3]
4. HTML reader ignores <b>, <i>, <sub>, <s>, highlight, footnotes, header/footer when opening .html it wrote itself. [p3]
5. Command walk never visits Table Design, Table Layout, Header & Footer, Equation, Chart Design, SmartArt Design tabs (excluded, no setup). Coverage gap.
6. engine toggle("bold") (unknown name) writes an invalid <bold/> element into the docx — macros can corrupt files. [p3 first run]
