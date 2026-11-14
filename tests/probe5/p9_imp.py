import os as _o; TESTS = _o.environ["FOLIO_WRITER_TESTS"]; exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read()); exec(open("/tmp/p5/probes/ph.py").read())
def a():
    yield 0.5
    for f in ("sections.docx", "lo/sections.doc", "lo/sections.odt", "lo/sections.rtf", "breaks.docx", "lo/breaks.odt", "tables.docx", "lo/tables.rtf", "lo/61745.odt", "61745.docx"):
        win.open_file("/tmp/corpus/" + f); yield 1.5
        e = ed(); n = e.page_count()
        hf = [e.page_hf_text(i) for i in range(n)]
        sizes = [tuple(round(v) for v in e.page_size(i)) for i in range(n)]
        x = doc_xml()["word/document.xml"]
        note(f, "pages=%d sizes=%s hf=%s | pagebreaks=%d colbreaks=%d pbb=%d sect=%d tbl=%d tc=%d drawing=%d" % (
            n, sorted(set(sizes)), hf[:6], len(re.findall(r'<w:br w:type="page"', x)), len(re.findall(r'<w:br w:type="column"', x)),
            cnt(x, "w:pageBreakBefore"), cnt(x, "w:sectPr"), cnt(x, "w:tbl"), cnt(x, "w:tc"), cnt(x, "w:drawing")))
        shot("imp_" + f.replace("/", "_").replace(".", "_"))
import re
run_scenarios(a)
