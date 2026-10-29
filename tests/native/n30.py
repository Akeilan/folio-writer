import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
# 2.31: OpenDocument text and Word 97-2003 opened by Folio itself (no converter),
# .odt saved by Folio itself, a .doc saved as .docx, the gallery's .ott templates
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


def a():
    yield 1.0
    # ---- .odt opens without LibreOffice
    win.open_file(os.path.join(DATA, "sample.odt")); yield 2.0
    ed = E.ed
    check("odt opened", "Import test" in body(ed), body(ed)[:3])
    check("odt format kept", E.format == "odt", E.format)
    check("odt title has no compatibility mode", "Compatibility" not in win.get_title(), win.get_title())
    check("odt heading style", ed.headings() and "Import test" in str(ed.headings()[0]), ed.headings()[:2])
    check("no converter run on open", not CALLS, CALLS)
    shot("n30_odt"); yield 0.2
    # ---- edit and save: the .odt is written by Folio
    ed.move_caret("doc_start", False)
    ed.type_text("Edited ")
    E.view.after_edit(); yield 0.3
    out = "/tmp/n30_saved.odt"
    shutil.copy(os.path.join(DATA, "sample.odt"), out)
    E.path = out
    ok = win.save(); yield 1.0
    check("odt saved", ok, MSG)
    z = zipfile.ZipFile(out)
    check("saved file is OpenDocument", z.read("mimetype") == b"application/vnd.oasis.opendocument.text")
    check("saved text", b"Edited Import test" in z.read("content.xml"))
    check("no converter run on save", not CALLS, CALLS)
    # ---- reopen what was saved
    win.open_file(out); yield 2.0
    check("saved odt reopens", "Edited Import test" in body(E.ed), body(E.ed)[:2])
    check("lists survive", all(t in body(E.ed) for t in ("First bullet", "Nested bullet", "Second number")), body(E.ed))
    check("footnote survives", E.ed.note_count(False) == 1, E.ed.note_count(False))
    check("comment survives", len(E.ed.comments()) == 1, E.ed.comments())
    win.engine.ed.mark_saved()
    # ---- .doc opens without LibreOffice, in Compatibility Mode
    win.open_file(os.path.join(DATA, "sample.doc")); yield 2.0
    check("doc opened", "Import test" in body(E.ed), body(E.ed)[:3])
    check("doc compatibility mode", "Compatibility Mode" in win.get_title(), win.get_title())
    check("no converter run for .doc", not CALLS, CALLS)
    shot("n30_doc"); yield 0.2
    # ---- Save on a .doc: saved in place as Word 97-2003, by Folio itself (W3-06)
    import shutil as _sh
    _sh.copy(os.path.join(DATA, "sample.doc"), "/tmp/n30_copy.doc")
    win.open_file("/tmp/n30_copy.doc"); yield 2.0
    asked = []

    def save_file(name, fmt=None):
        asked.append(fmt)
        return None
    win.dialogs.save_file = save_file
    ok = win.save(); yield 1.0
    check("doc saved in place", ok and not asked, (ok, asked))
    with open("/tmp/n30_copy.doc", "rb") as fh:
        check("still a Word 97-2003 file", fh.read(8) == bytes.fromhex("d0cf11e0a1b11ae1"))
    check("no converter run for .doc save", not CALLS, CALLS)
    win.open_file("/tmp/n30_copy.doc"); yield 2.0
    check("saved doc reopens", "Import test" in body(E.ed), body(E.ed)[:3])
    # ---- the gallery's templates (.ott) open as new documents
    from folio import SHARE
    gal = os.path.join(SHARE, "templates", "gallery")
    otts = sorted(f for f in os.listdir(gal) if f.endswith(".ott")) if os.path.isdir(gal) else []
    for f in otts[:3]:
        win.new_document(os.path.join(gal, f)); yield 1.5
        check("template %s opens" % f, E.ed is not None and E.is_new and len(body(E.ed)) >= 1, f)
    check("no converter run for templates", not CALLS, CALLS)
    win.engine.ed.mark_saved()


run_scenarios(a)
