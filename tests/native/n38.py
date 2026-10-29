import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
# 2.32 (W3-01): Rich Text Format opened and saved by Folio itself, with no LibreOffice
import os
import shutil
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
    p = "/tmp/n38_check.docx"
    ed.save(p)
    z = zipfile.ZipFile(p)
    return {n: z.read(n).decode("utf-8", "replace") for n in z.namelist() if n.endswith((".xml", ".rels"))}


def check_sample(where):
    ed = E.ed
    b = body(ed)
    x = xml_of(ed)
    doc = x.get("word/document.xml", "")
    check(where + ": text", any(t.endswith("RTF import test") for t in b) and any("strong red" in t for t in b), b[:3])
    check(where + ": accented and euro", any("café € euro" in t for t in b), [t for t in b if "caf" in t])
    check(where + ": heading style", "RTF import test" in str(ed.headings()), ed.headings()[:2])
    check(where + ": bold, italic, red", "<w:b/>" in doc and "<w:i/>" in doc and 'w:val="C00000"' in doc)
    check(where + ": character style", "StrongRed" in doc, "")
    check(where + ": lists", "word/numbering.xml" in x and doc.count("<w:numPr>") >= 4, doc.count("<w:numPr>"))
    check(where + ": bullet", "•" in x.get("word/numbering.xml", ""))
    check(where + ": table with merged and shaded cell", "Cell A1" in doc and "<w:tbl>" in doc and "w:vMerge" in doc and "FFF2CC" in doc)
    check(where + ": footnote", ed.note_count(False) == 1, ed.note_count(False))
    check(where + ": link", "https://example.org/" in x.get("word/_rels/document.xml.rels", ""))
    check(where + ": bookmark", "mark1" in ed.bookmark_names(), ed.bookmark_names())
    check(where + ": comment", len(ed.comments()) == 1 and "A comment." in str(ed.comments()), ed.comments())
    check(where + ": picture", any(n.startswith("word/media/") for n in zipfile.ZipFile("/tmp/n38_check.docx").namelist()))
    check(where + ": header", "Page header text" in "".join(v for k, v in x.items() if "header" in k))
    check(where + ": two sections, the second landscape", ed.section_count() == 2 and 'w:orient="landscape"' in doc, ed.section_count())
    check(where + ": title", "RTF import test" in x.get("docProps/core.xml", ""))


def a():
    yield 1.0
    src = "/tmp/n38_sample.rtf"
    shutil.copy(os.path.join(DATA, "sample.rtf"), src)
    win.open_file(src); yield 2.0
    check("rtf opened", E.ed is not None and "RTF import test" in body(E.ed), body(E.ed)[:3] if E.ed else None)
    check("rtf format kept", E.format == "rtf", E.format)
    check_sample("opened")
    check("no converter run on open", not CALLS, CALLS)
    shot("n38_rtf"); yield 0.2
    # ---- edit and Save: the .rtf is written by Folio
    ed = E.ed
    ed.move_caret("doc_start", False)
    ed.type_text("Edited ")
    E.view.after_edit(); yield 0.3
    ok = win.save(); yield 1.0
    check("rtf saved", ok, MSG)
    data = open(src, "rb").read()
    check("saved file is RTF", data.startswith(b"{\\rtf1"), data[:20])
    check("no converter run on save", not CALLS, CALLS)
    win.open_file(src); yield 2.0
    check("saved rtf reopens", "Edited RTF import test" in body(E.ed), body(E.ed)[:2])
    check_sample("reopened")
    E.ed.mark_saved()
    # ---- Save As .rtf from a new document
    win.app.new_window()
    yield 1.5
    w2 = win.app.windows[-1]
    e2 = w2.engine
    e2.ed.type_text("Fresh document")
    e2.view.after_edit(); yield 0.3
    out = "/tmp/n38_new.rtf"
    if os.path.exists(out):
        os.remove(out)
    ok = w2.save_to(out); yield 1.0
    check("Save As .rtf", ok and open(out, "rb").read().startswith(b"{\\rtf1"), ok)
    check("its text", b"Fresh document" in open(out, "rb").read())
    e2.ed.mark_saved()
    check("no converter at all", not CALLS, CALLS)


run_scenarios(a)
