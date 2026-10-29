import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
def fid():
    win.open_file("/tmp/wfid/fid.docx"); yield 4.0
    for p in top_paras():
        Rng((p, 0)).select()
        note("para", (caret_page() + 1, ptext(p)[:30], E.ed.current_section()))
    note("pages", pages())
    for c in comments():
        note("comment", (c["author"], repr(c["text"]), c["date"]))
    for i in range(page_setup()["section_count"]):
        ps = page_setup(i)
        note("section", (i, ps["width"] > ps["height"], ps["title_pg"]))
run_scenarios(fid)
