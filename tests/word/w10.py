import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
def d():
    win.open_file("/tmp/wfid2/fid2.docx"); yield 6.0
    check("footnote", notes() == 1 and "footnote text" in part_text("word/footnotes.xml"), notes())
    check("endnote", notes(True) == 1, notes(True))
    rl = [(c[0], c[1]) for c in changes()]
    check("tracked changes with authors", any(k.lower().startswith("ins") and a == "Alice" for k, a in rl) and any(k.lower().startswith("del") and a == "Bob" for k, a in rl), rl)
    ccs = len(E.ed.content_controls())
    check("content controls (3)", ccs >= 3, ccs)
    info = [object_info(o[0]) for o in objects("Picture")]
    check("floating picture right, square wrap", any(not i["inline"] and i["wrap"] in ("square", "tight") for i in info), info)
    note("objects", objects())
    check("text box present", any(o[1].startswith("Text Box") for o in objects()), objects())
    dc = drop_caps()
    note("drop cap paras", dc)
    check("drop cap imported", bool(dc), dc)
    bms = E.ed.bookmark_names()
    check("bookmark Target1", "Target1" in bms, bms)
    hdrs = parts_text("word/header")
    note("headers", hdrs)
    check("first/even/odd headers", any("First page header" in h for h in hdrs) and any("Even page header" in h for h in hdrs), hdrs)
    nsec = page_setup()["section_count"]
    check("page border", any(E.ed.page_borders_xml(i) for i in range(nsec)), [E.ed.page_borders_xml(i)[:60] for i in range(nsec)])
    cols = [page_setup(i)["cols"] for i in range(nsec)]
    check("two-column section", 2 in cols, cols)
    ln = [part_xml("word/document.xml").count("w:lnNumType")]
    check("line numbering on", ln[0] > 0, ln)
    note("pages", pages())
    for i in (1, 2, 3):
        E.ed.goto_page(i - 1); E.view.after_move(); yield 1.0
        shot("w10_p%d" % i)
    ok = win.save_to("/tmp/wfid2/fid2_out.docx"); yield 3.0
    note("saved", ok)
run_scenarios(d)
