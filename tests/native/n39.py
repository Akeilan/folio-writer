import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
# 2.32 (W3-05, W3-06): Word 6.0/95 documents opened, and Word 97-2003 .doc/.dot saved, by
# Folio itself with no LibreOffice
import os
import shutil
import struct
import subprocess
import zipfile

DATA = TESTS + "/data/import"
CALLS = []
_run = subprocess.run


def run_spy(args, *a, **k):
    if args and "soffice" in str(args[0]):
        CALLS.append(args)
    return _run(args, *a, **k)


subprocess.run = run_spy
_which = shutil.which
shutil.which = lambda name, *a, **k: None if name in ("soffice", "libreoffice") else _which(name, *a, **k)
MSG = []
win.dialogs.message = lambda text, *a, **k: MSG.append(text)


def body(ed):
    return [ed.para_text_of(n) for k, n, _t in ed.body_blocks() if k == "p"]


def xml_of(ed):
    p = "/tmp/n39_check.docx"
    ed.save(p)
    z = zipfile.ZipFile(p)
    return {n: z.read(n).decode("utf-8", "replace") for n in z.namelist() if n.endswith((".xml", ".rels"))}


def check_word6(where):
    ed = E.ed
    b = body(ed)
    x = xml_of(ed)
    doc = x.get("word/document.xml", "")
    check(where + ": text", any("Word 6 import test" in t for t in b) and any("Plain then bold" in t for t in b), b[:3])
    check(where + ": heading", "Word 6 import test" in str(ed.headings()), ed.headings()[:2])
    check(where + ": bold, italic, red 14 pt", "<w:b/>" in doc and "<w:i/>" in doc and 'w:val="FF0000"' in doc
          and 'w:sz w:val="28"' in doc)
    check(where + ": justified", 'w:jc w:val="both"' in doc)
    check(where + ": bulleted list", doc.count("<w:numPr>") >= 2 and "•" in x.get("word/numbering.xml", ""),
          doc.count("<w:numPr>"))
    check(where + ": table", "<w:tbl>" in doc and all(c in doc for c in ("A1", "B1", "A2", "B2")))
    check(where + ": footnote", ed.note_count(False) == 1 and "Note text" in x.get("word/footnotes.xml", ""),
          ed.note_count(False))
    check(where + ": header", "Header text" in "".join(v for k, v in x.items() if "header" in k))
    check(where + ": two sections, the second landscape", ed.section_count() == 2 and 'w:orient="landscape"' in doc,
          ed.section_count())


def nfib(path):
    from folio.native.docread import CFB
    wd = CFB(open(path, "rb").read()).stream("WordDocument")
    return struct.unpack_from("<HHH", wd, 0), struct.unpack_from("<H", wd, 0x0A)[0]


def a():
    yield 1.0
    src = "/tmp/n39_word6.doc"
    shutil.copy(os.path.join(DATA, "sample6.doc"), src)
    check("fixture is Word 6", nfib(src)[0][:2] == (0xA5DC, 0x65), nfib(src))
    win.open_file(src); yield 2.0
    check("word 6 opened", E.ed is not None and any("Word 6 import test" in t for t in body(E.ed)),
          (win.engine.open_error, body(E.ed)[:3] if E.ed else None))
    check("compatibility mode", "Compatibility Mode" in win.get_title(), win.get_title())
    check_word6("opened")
    check("no converter run on open", not CALLS, CALLS)
    shot("n39_word6"); yield 0.2
    # ---- Save: written as Word 97-2003 (as Word itself saves an older file)
    ed = E.ed
    ed.move_caret("doc_start", False)
    ed.type_text("Edited ")
    E.view.after_edit(); yield 0.3
    ok = win.save(); yield 1.0
    check("saved", ok, MSG)
    (wi, nf, _x), flags = nfib(src)
    check("saved as Word 97-2003", wi == 0xA5EC and nf == 0xC1, (hex(wi), hex(nf)))
    check("no converter run on save", not CALLS, CALLS)
    win.open_file(src); yield 2.0
    check("saved doc reopens", any("Edited Word 6 import test" in t for t in body(E.ed)), body(E.ed)[:2])
    check_word6("reopened")
    E.ed.mark_saved()
    # ---- the full sample through Save As .doc, then reopened
    win.open_file(os.path.join(DATA, "sample.docx")); yield 2.0
    before = xml_of(E.ed)
    text0 = [t for t in body(E.ed) if t.strip()]
    out = "/tmp/n39_sample.doc"
    if os.path.exists(out):
        os.remove(out)
    ok = win.save_to(out); yield 1.0
    check("Save As .doc", ok and nfib(out)[0][1] == 0xC1, ok)
    check("now a .doc", E.format == "doc", E.format)
    win.open_file(out); yield 2.0
    after = xml_of(E.ed)
    d0, d1 = before.get("word/document.xml", ""), after.get("word/document.xml", "")
    for what, probe in (("table", "<w:tbl>"), ("list", "<w:numPr>"), ("bold", "<w:b/>")):
        check("doc keeps " + what, (probe in d0) == (probe in d1), what)
    text1 = [t for t in body(E.ed) if t.strip()]
    check("doc keeps the text", text0 == text1, [(x, y) for x, y in zip(text0, text1) if x != y][:2])
    check("doc keeps footnotes", E.ed.note_count(False) == before.get("word/footnotes.xml", "").count("<w:footnote ") - 2
          or E.ed.note_count(False) >= 1, E.ed.note_count(False))
    E.ed.mark_saved()
    # ---- Save As template 97-2003 (.dot)
    out = "/tmp/n39_sample.dot"
    if os.path.exists(out):
        os.remove(out)
    ok = win.save_to(out); yield 1.0
    check("Save As .dot", ok and os.path.exists(out) and nfib(out)[1] & 1, ok)
    E.ed.mark_saved()
    check("no converter at all", not CALLS, CALLS)


run_scenarios(a)
