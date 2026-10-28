"""Folio's own OpenDocument and Word 97-2003 readers, and the OpenDocument writer, checked
against the engine (no window). Run in the build root: python3 tests/import_test.py
Prints PASS/FAIL lines; exit code 1 on any failure."""
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "app"))
import folio_core  # noqa: E402
from folio.native import importers, odfwrite, docxread, odfread, docread  # noqa: E402

DATA = os.path.join(HERE, "data", "import")
FAILS = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else " | " + str(detail)))
    if not cond:
        FAILS.append(name)


def open_imported(path):
    tmp = tempfile.mkdtemp(prefix="fw-imp-")
    return folio_core.Editor.open(importers.to_docx(path, os.path.join(tmp, "x.docx")))


def body(ed):
    out = []
    for kind, node, ti in ed.body_blocks():
        if kind == "p":
            out.append(ed.para_text_of(node))
        else:
            for row in ed.table_cells(ti):
                out.append("|".join(" ".join(ed.para_text_of(p) for p in cell) for cell in row))
    return out


def features(label, ed):
    text = body(ed)
    joined = "\n".join(text)
    check(label + ": heading text", "Import test" in text, text[:3])
    check(label + ": runs", "Plain, bold, italic and red underlined text with a note" in joined.replace("￼", ""), text[:3])
    check(label + ": list items", all(t in text for t in ("First bullet", "Nested bullet", "Second number")), text)
    check(label + ": table cells", any("A1" in t and "B1" in t for t in text) and any("Merged across" in t for t in text), text)
    check(label + ": two pages", ed.page_count() == 2, ed.page_count())
    check(label + ": footnote", ed.note_count(False) == 1, ed.note_count(False))
    cs = ed.comments()
    check(label + ": comment", len(cs) == 1 and "A comment." in str(cs[0]), cs)
    objs = [o for o in ed.objects_list() if o[2] == "Picture"]
    check(label + ": picture", len(objs) == 1, ed.objects_list())
    heads = ed.headings() if hasattr(ed, "headings") else []
    check(label + ": headings outline", any("Import test" in str(h) for h in heads) and any("Lists" in str(h) for h in heads), heads)
    check(label + ": header and footer on both pages", ed.page_hf(0) == (True, True) and ed.page_hf(1) == (True, True),
          (ed.page_hf(0), ed.page_hf(1)))


for name in ("sample.odt", "sample.doc"):
    p = os.path.join(DATA, name)
    try:
        features(name, open_imported(p))
    except Exception as e:
        import traceback
        traceback.print_exc()
        check(name + " opens", False, e)

# the writer: docx -> odt -> back, nothing lost
tmp = tempfile.mkdtemp(prefix="fw-odt-")
odt = os.path.join(tmp, "round.odt")
odfwrite.docx_to_odt(os.path.join(DATA, "sample.docx"), odt)
check("odt written is a zip with mimetype first",
      open(odt, "rb").read()[38:77] == b"application/vnd.oasis.opendocument.text")
features("round trip .odt", open_imported(odt))
# twice round: model stays stable
d1 = odfread.read(odt)
odt2 = os.path.join(tmp, "round2.odt")
dx = importers.to_docx(odt, os.path.join(tmp, "r.docx"))
odfwrite.docx_to_odt(dx, odt2)
d2 = odfread.read(odt2)
t1 = [x.get("text") for b in d1.all_blocks() for x in b["runs"] if x.get("t") == "text"]
t2 = [x.get("text") for b in d2.all_blocks() for x in b["runs"] if x.get("t") == "text"]
check("second round trip keeps every run", t1 == t2, (t1, t2))
# Word 95 and damaged files say so instead of crashing
bad = os.path.join(tmp, "bad.doc")
open(bad, "wb").write(b"not a word file")
try:
    docread.read(bad)
    check("damaged .doc refused", False)
except docread.Unsupported:
    check("damaged .doc refused", True)
print("DONE", "failures:", len(FAILS))
sys.exit(1 if FAILS else 0)
