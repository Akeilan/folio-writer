exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
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
