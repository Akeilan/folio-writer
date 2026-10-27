exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
def d():
    win.open_file("/tmp/wfid2/fid2.docx"); yield 6.0
    m = M()
    check("footnote", m.getFootnotes().getCount() == 1 and "footnote text" in m.getFootnotes().getByIndex(0).getString(), m.getFootnotes().getCount())
    check("endnote", m.getEndnotes().getCount() == 1, m.getEndnotes().getCount())
    rl = []; en = m.getRedlines().createEnumeration()
    while en.hasMoreElements():
        r = en.nextElement(); rl.append((r.RedlineType, r.RedlineAuthor))
    check("tracked changes with authors", ("Insert", "Alice") in rl and ("Delete", "Bob") in rl, rl)
    ccs = 0
    for p in paras():
        if not p.supportsService("com.sun.star.text.Paragraph"): continue
        pe = p.createEnumeration()
        while pe.hasMoreElements():
            if getattr(pe.nextElement(), "TextPortionType", "") == "ContentControl": ccs += 1
    check("content controls (3)", ccs >= 3, ccs)
    g = m.getGraphicObjects()
    info = [(g.getByIndex(i).AnchorType.value, g.getByIndex(i).TextWrap.value, g.getByIndex(i).HoriOrient) for i in range(g.getCount())]
    check("floating picture right, square wrap", any(a == "AT_CHARACTER" or a == "AT_PARAGRAPH" for a, w, h in info) and any(w in ("PARALLEL", "DYNAMIC") for a, w, h in info), info)
    shapes = M().getDrawPage().getCount()
    fr = m.getTextFrames().getElementNames()
    note("frames / shapes", (fr, shapes))
    tb = any("text box" in m.getDrawPage().getByIndex(i).getString().lower() if hasattr(m.getDrawPage().getByIndex(i), "getString") else False for i in range(shapes))
    check("text box text present", tb or any("Text inside" in m.getTextFrames().getByName(n).getString() for n in fr), "")
    dc = [p.DropCapFormat.Lines for p in paras() if p.supportsService("com.sun.star.text.Paragraph") and p.DropCapFormat.Lines > 0]
    note("drop cap paras", dc)
    check("drop cap imported", bool(dc) or any("D" == m.getTextFrames().getByName(n).getString() for n in fr), (dc, fr))
    bms = m.getBookmarks().getElementNames()
    check("bookmark Target1", "Target1" in bms, bms)
    ps = m.getStyleFamilies().getByName("PageStyles")
    used = [n for n in ps.getElementNames() if ps.getByName(n).isInUse()]
    hdrs = []
    for n in used:
        s = ps.getByName(n)
        hdrs.append((n, s.HeaderIsOn and s.HeaderText.getString(), s.HeaderIsOn and not s.HeaderIsShared and s.HeaderTextLeft.getString(), s.HeaderIsOn and getattr(s, "FirstIsShared", True) is False and s.HeaderTextFirst.getString(), s.LeftBorder.OuterLineWidth, s.TextColumns.ColumnCount))
    note("page styles", hdrs)
    check("first/even/odd headers", any("First page header" in str(h) for h in hdrs) and any("Even page header" in str(h) for h in hdrs), hdrs)
    check("page border", any(h[4] > 0 for h in hdrs), hdrs)
    secs = [m.getTextSections().getByIndex(i).TextColumns.ColumnCount for i in range(m.getTextSections().getCount())]
    check("two-column section", any(h[5] == 2 for h in hdrs) or 2 in secs, (hdrs, secs))
    ln = m.getLineNumberingProperties()
    check("line numbering on", ln.IsOn, ln.IsOn)
    vc().jumpToLastPage(); note("pages", vc().getPage())
    for i in (1, 2, 3):
        vc().jumpToPage(i); vc().jumpToStartOfPage(); yield 1.0
        shot("w10_p%d" % i)
    ok = win.save_to("/tmp/wfid2/fid2_out.docx"); yield 3.0
    note("saved", ok)
run_scenarios(d)
