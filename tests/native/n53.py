import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
# W5-06: Arabic and Hebrew laid out right to left, shaped in context, and
# selectable; left-to-right text untouched.
AR = "سلام"
HE = "שלום"

def boxes(s):
    """(x, width) of each character of the one paragraph, in logical order."""
    ed = E.ed
    ed.select_all(); ed.delete(True, False)
    ed.type_text(s)
    E.view.after_edit()
    p = ed.body_blocks()[0][1]
    out = []
    for i in range(len(s)):
        r = ed.range_rects(p, i, p, i + 1)
        out.append((r[0][1], r[0][3]) if r else None)
    return out

def tiles(bs):
    """Do the characters tile their line with no gap and no overlap?"""
    edges = sorted((x, x + w) for x, w in bs)
    return all(abs(edges[i][1] - edges[i + 1][0]) < 0.05 for i in range(len(edges) - 1))

def a():
    yield 1.0
    focus(); yield 0.2
    ed = E.ed
    for name, s in (("arabic", AR), ("hebrew", HE)):
        bs = boxes(s); yield 0.3
        check("%s: every character placed" % name, all(bs) and all(w > 0 for _x, w in bs), str(bs))
        check("%s: right to left" % name, all(bs[i][0] > bs[i + 1][0] for i in range(len(bs) - 1)), str(bs))
        check("%s: no gaps" % name, tiles(bs), str(bs))
    lat = boxes("abc"); yield 0.3
    check("latin: left to right", all(lat[i][0] < lat[i + 1][0] for i in range(len(lat) - 1)), str(lat))
    check("latin: no gaps", tiles(lat), str(lat))
    # contextual shaping: a joined pair is not two isolated letters
    one = boxes("ب"); yield 0.2
    two = boxes("بب"); yield 0.2
    pair = two[0][1] + two[1][1]
    check("arabic letters join", abs(pair - 2 * one[0][1]) > 1.0, "isolated %.2f, pair %.2f" % (one[0][1], pair))
    check("joined forms are narrower", pair < 2 * one[0][1], "%.2f < %.2f" % (pair, 2 * one[0][1]))
    # a right-to-left stretch inside left-to-right text
    mix = "Hi " + HE + " go"
    bs = boxes(mix); yield 0.3
    he = bs[3:7]
    check("mixed: the hebrew runs right to left", all(he[i][0] > he[i + 1][0] for i in range(len(he) - 1)), str(he))
    check("mixed: the latin runs left to right", bs[0][0] < bs[1][0] < bs[2][0] and bs[8][0] < bs[9][0], str(bs))
    check("mixed: hebrew sits between the latin", bs[2][0] < min(x for x, _w in he)
          and max(x + w for x, w in he) <= bs[8][0] + 0.05, str(bs))
    check("mixed: no gaps", tiles(bs), str(bs))
    # selecting right-to-left text highlights it
    ed.select_all(); ed.delete(True, False)
    ed.type_text(HE); E.view.after_edit(); yield 0.3
    p = ed.body_blocks()[0][1]
    rects = ed.range_rects(p, 0, p, 4)
    check("selection of hebrew has width", rects and all(r[3] > 0 for r in rects), str(rects))
    wide = sum(r[3] for r in rects)
    bs = boxes(HE); yield 0.3
    check("selection covers the text", abs(wide - sum(w for _x, w in bs)) < 0.5, "%.2f" % wide)
    ed.select_all(); ed.delete(True, False)
    ed.type_text("Hi " + HE + " go"); E.view.after_edit(); yield 0.3
    p = ed.body_blocks()[0][1]
    # "Hi " then the first hebrew letter, which sits at the far right of its
    # run: two separated pieces, with the rest of the hebrew between them
    r2 = ed.range_rects(p, 0, p, 4)
    check("a range across directions is in pieces", len(r2) == 2, str(r2))
    check("the pieces are apart", len(r2) == 2 and r2[1][1] > r2[0][1] + r2[0][3] + 1.0, str(r2))
    # a range that is visually one stretch stays one rectangle
    check("a contiguous range is one piece", len(ed.range_rects(p, 1, p, 9)) == 1, str(ed.range_rects(p, 1, p, 9)))
    # a right-to-left paragraph sits against the right margin
    ed.select_all(); ed.delete(True, False)
    ed.type_text(AR); E.view.after_edit(); yield 0.2
    left_x = boxes(AR)[-1][0]; yield 0.2
    ed.apply_para([("w:bidi", [])], "Right to Left"); E.view.after_edit(); yield 0.4
    p = ed.body_blocks()[0][1]
    rtl_x = ed.range_rects(p, 3, p, 4)[0][1]
    check("w:bidi right aligns the paragraph", rtl_x > left_x + 50, "%.2f -> %.2f" % (left_x, rtl_x))
    ed.undo(); E.view.after_edit(); yield 0.3
    # a click at the right-hand end of Arabic puts the caret at the start
    ed.select_all(); ed.delete(True, False)
    ed.type_text(AR); E.view.after_edit(); yield 0.3
    p = ed.body_blocks()[0][1]
    r = ed.range_rects(p, 0, p, 1)[0]
    sx, sy = doc_screen((r[1] + r[3] - 0.4) * 20, (r[2] + 4) * 20)
    click(sx, sy); yield 0.5
    check("click at the right end lands at the start", ed.caret_pos()[1] == 0, str(ed.caret_pos()))
    r = ed.range_rects(p, 3, p, 4)[0]
    sx, sy = doc_screen((r[1] + 0.4) * 20, (r[2] + 4) * 20)
    click(sx, sy); yield 0.5
    check("click at the left end lands at the end", ed.caret_pos()[1] == 4, str(ed.caret_pos()))
    # the characters survive a save and reopen
    win.save_to("/tmp/n53.docx"); yield 0.6
    import zipfile
    d = zipfile.ZipFile("/tmp/n53.docx").read("word/document.xml").decode()
    check("arabic saved", AR in d)
    E.ed.mark_saved()

run_scenarios(a)
