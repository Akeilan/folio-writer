import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
# 2.33.3 (W3-11): a saved .doc read back elsewhere keeps links, the italic after an empty
# unknown field, and AUTHOR results (the author property is filled from the field when unset)
import os
import shutil
import subprocess
import zipfile

DATA = os.path.join(TESTS, "data")


def xml_of(ed):
    p = "/tmp/n45_check.docx"
    ed.save(p)
    z = zipfile.ZipFile(p)
    return {n: z.read(n).decode("utf-8", "replace") for n in z.namelist() if n.endswith((".xml", ".rels"))}


def a():
    yield 1.0
    out = "/tmp/n45.doc"
    if os.path.exists(out):
        os.remove(out)
    win.open_file(os.path.join(DATA, "w311.docx")); yield 2.0
    ok = win.save_to(out); yield 1.0
    check("saved .doc", ok and os.path.exists(out), ok)
    win.open_file(out); yield 2.0
    x = xml_of(E.ed)
    d = x.get("word/document.xml", "")
    check("links kept", d.count("<w:hyperlink") + d.count("HYPERLINK") >= 3, d.count("HYPERLINK"))
    i = d.find("ItalicAfter2")
    check("italic after empty field", i > 0 and "<w:i/>" in d[max(0, i - 300):i], d[max(0, i - 300):i])
    check("AUTHOR result kept", d.count("Jane Writer") >= 2, d.count("Jane Writer"))
    check("author property filled", "Jane Writer" in x.get("docProps/core.xml", ""), x.get("docProps/core.xml", "")[:300])
    E.ed.mark_saved()
    # read back in the office suite, where one is installed
    if shutil.which("soffice"):
        od = "/tmp/n45_lo"
        shutil.rmtree(od, ignore_errors=True)
        subprocess.run(["timeout", "180", "soffice", "-env:UserInstallation=file:///tmp/n45_prof", "--headless",
                        "--convert-to", "odt", "--outdir", od, out], capture_output=True)
        odt = os.path.join(od, "n45.odt")
        if os.path.exists(odt):
            z = zipfile.ZipFile(odt)
            meta, content = z.read("meta.xml").decode(), z.read("content.xml").decode()
            check("office suite: author", "initial-creator>Jane Writer<" in meta
                  or content.count("Jane Writer") >= 2, meta[-300:])
            check("office suite: italic kept", "ItalicAfter2" in content)


run_scenarios(a)
