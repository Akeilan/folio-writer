exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())

def tables():
    fresh(); yield 0.3
    T("Before"); K("Return"); yield 0.3
    from folio import docapi as D
    win.actions.cmd(".uno:InsertTable", {"Columns": 3, "Rows": 2}) ; yield 1.0
    tt = M().getTextTables()
    check("insert 3x2 table", tt.getCount() == 1, tt.getCount())
    if not tt.getCount(): return
    t = tt.getByIndex(0)
    T("a"); K("Tab"); T("b"); K("Tab"); T("c"); K("Tab"); T("d"); yield 0.6
    check("Tab moves to next cell", t.getCellByName("B1").getString() == "b" and t.getCellByName("A2").getString() == "d", [t.getCellByName(n).getString() for n in ("A1","B1","C1","A2")])
    K("shift+Tab"); yield 0.3
    note("shift+tab selects previous cell?", repr(sel()))
    K("ctrl+End"); yield 0.3
    # last cell -> Tab adds row
    c = vc(); c.gotoRange(t.getCellByName("C2").getText().getEnd(), False); yield 0.3
    K("Tab"); yield 0.6
    check("Tab in last cell adds a row", t.getRows().getCount() == 3, t.getRows().getCount())
    T("x"); K("Return"); T("y"); yield 0.5
    check("Enter in cell = new paragraph in cell", "\n" in t.getCellByName("A3").getString(), repr(t.getCellByName("A3").getString()))
    # ctrl+tab inserts tab char in cell
    K("ctrl+Tab"); yield 0.3
    check("ctrl+Tab inserts tab in cell", "\t" in t.getCellByName("A3").getString(), repr(t.getCellByName("A3").getString()))
    # alt+shift+up moves row up
    K("alt+shift+Up"); yield 0.5
    note("alt+shift+up row move", [t.getCellByName("A%d" % i).getString() for i in (1, 2, 3)])
    check("alt+shift+Up moves table row up", t.getCellByName("A2").getString().lower().startswith("x"), [t.getCellByName("A%d" % i).getString() for i in (1, 2, 3)])
    shot("w3_table")
    # select whole table and press Backspace -> deletes table (Word)
    c = vc(); c.gotoRange(t.getCellByName("A1").getText().getStart(), False)
    K("ctrl+a"); yield 0.3
    note("ctrl+a in table selects", repr(sel())[:40])
    # table select via Layout > Select > Select Table then Backspace
    rib("Table Layout", "Select", "Select Table"); yield 0.6
    K("BackSpace"); yield 0.6
    check("Select Table + Backspace deletes table", M().getTextTables().getCount() == 0, M().getTextTables().getCount())
    # Enter at start of first cell of table at doc start inserts paragraph before table
    fresh(); yield 0.3
    win.actions.cmd(".uno:InsertTable", {"Columns": 2, "Rows": 2}); yield 0.8
    c = vc(); c.gotoStart(False); yield 0.2
    K("Return"); yield 0.5
    check("Enter at start of table at top inserts paragraph above", paras()[0].supportsService("com.sun.star.text.Paragraph"), [type(p).__name__ for p in paras()])

def references():
    fresh(); yield 0.3
    for i, h in enumerate(("Intro", "Methods", "Results")):
        T(h); K("ctrl+alt+1"); K("Return"); T("Body text %d." % i); K("Return"); yield 0.3
    yield 0.5
    vc().gotoStart(False); yield 0.2
    K("Return"); K("ctrl+Home"); yield 0.3
    rib("References", "Table of Contents", "Automatic Table 1") or rib("References", "Table of Contents", "Automatic Table"); yield 1.5
    idx = M().getDocumentIndexes()
    check("insert TOC", idx.getCount() == 1, idx.getCount())
    if idx.getCount():
        s = idx.getByIndex(0).getAnchor().getString()
        check("TOC lists headings", all(h in s for h in ("Intro", "Methods", "Results")), repr(s[:120]))
        # rename a heading then update
        r = find("Methods", 1) or find("Methods")
        sd = M().createSearchDescriptor(); sd.SearchString = "Results"
        allr = M().findAll(sd)
        allr.getByIndex(allr.getCount() - 1).setString("Findings")
        rib("References", "Update Table"); yield 1.5
        for d in dialogs_open(): note("update dialog", d.get_title())
        respond("Update", Gtk.ResponseType.OK); yield 1.0
        s = idx.getByIndex(0).getAnchor().getString()
        check("Update Table refreshes TOC", "Findings" in s, repr(s[:120]))
        shot("w3_toc")
    # footnotes
    K("ctrl+End"); T("Claim"); K("ctrl+alt+f"); yield 1.0
    T("Footnote text."); yield 0.4
    check("footnote inserted and typing goes into it", M().getFootnotes().getCount() == 1 and "Footnote text" in M().getFootnotes().getByIndex(0).getString(), M().getFootnotes().getCount())
    shot("w3_footnote")
    # caption
    fresh(); yield 0.3
    rib("References", "Insert Caption"); yield 1.2
    note("caption dialog", [d.get_title() for d in dialogs_open()])
    respond("Caption", Gtk.ResponseType.OK); yield 0.8
    note("after caption", para_texts())
    check("Insert Caption adds 'Figure 1'", "Figure 1" in text() or "Table 1" in text() or "Equation 1" in text(), para_texts())

def review():
    fresh(); yield 0.3
    T("Original sentence here."); yield 0.4
    K("ctrl+shift+e"); yield 0.5
    check("ctrl+shift+e turns on Track Changes", bool(M().RecordChanges), M().RecordChanges)
    K("ctrl+Home"); T("New "); yield 0.4
    K("End"); K("BackSpace"); yield 0.4
    n = 0; en = M().getRedlines().createEnumeration()
    while en.hasMoreElements(): en.nextElement(); n += 1
    check("tracked insertion + deletion recorded", n >= 2, n)
    shot("w3_track")
    rib("Review", "Accept", "Accept All Changes"); yield 0.8
    n = 0; en = M().getRedlines().createEnumeration()
    while en.hasMoreElements(): en.nextElement(); n += 1
    check("Accept All Changes clears redlines", n == 0, n)
    K("ctrl+shift+e"); yield 0.3
    # comments
    docapi.controller(M()).select(find("Original")); yield 0.3
    rib("Review", "New Comment"); yield 1.0
    T("My comment"); K("ctrl+Return"); yield 1.2
    fields = []
    en = M().getTextFields().createEnumeration()
    while en.hasMoreElements():
        f = en.nextElement()
        if f.supportsService("com.sun.star.text.textfield.Annotation"): fields.append(f)
    check("comment created with text", len(fields) == 1 and fields[0].Content == "My comment", [f.Content for f in fields])
    shot("w3_comment")
    # word count
    rib("Review", "Word Count"); yield 1.0
    check("Word Count dialog", bool(dlg("Word Count")), [d.get_title() for d in dialogs_open()])
    close_dialogs(); yield 0.4
    # spelling dialog
    fresh(); yield 0.3
    T("This has a mistaek in it. "); yield 0.5
    focus(); K("F7"); yield 1.5
    shot("w3_spell")
    note("F7 opens", [d.get_title() for d in dialogs_open()] + ["pane:%s" % [type(p).__name__ for p in getattr(win, 'panes', [])]])
    close_dialogs(); K("Escape"); yield 0.4
    focus(); docapi.controller(M()).select(find("This")); yield 0.3
    K("shift+F7"); yield 1.2
    shot("w3_thesaurus")
    note("shift+F7 opens", [d.get_title() for d in dialogs_open()])
    close_dialogs(); yield 0.3

def layout():
    fresh(); yield 0.3
    T("Page one text."); yield 0.3
    rib("Layout", "Orientation", "Landscape"); yield 0.8
    ps = docapi.page_setup(M())
    check("Orientation Landscape", ps["landscape"], ps)
    rib("Layout", "Orientation", "Portrait"); yield 0.6
    rib("Layout", "Margins", "Narrow"); yield 0.6
    ps = docapi.page_setup(M())
    check("Margins Narrow (1.27cm)", abs(ps["left"] - 1270) < 20, (ps["left"], ps["top"]))
    rib("Layout", "Columns", "Two"); yield 0.6
    ok = False
    try:
        ps2 = M().getStyleFamilies().getByName("PageStyles").getByName(vc().PageStyleName)
        ok = ps2.TextColumns.ColumnCount == 2
    except Exception as e:
        ok = str(e)
    sec = vc().TextSection
    check("Columns Two", ok is True or (sec is not None and sec.TextColumns.ColumnCount == 2), ok)
    rib("Layout", "Columns", "One"); yield 0.5
    K("End"); rib("Layout", "Breaks", "Next Page"); yield 0.8
    T("Section two"); yield 0.3
    rib("Layout", "Orientation", "Landscape"); yield 0.8
    c = vc(); c.jumpToFirstPage(); yield 0.3
    note("page styles", [vc().PageStyleName])
    p1 = M().getStyleFamilies().getByName("PageStyles").getByName(vc().PageStyleName).IsLandscape
    c.jumpToLastPage(); yield 0.3
    p2 = M().getStyleFamilies().getByName("PageStyles").getByName(vc().PageStyleName).IsLandscape
    check("section-level orientation (page 1 portrait, page 2 landscape)", (not p1) and p2, (p1, p2))
    shot("w3_sections")
    rib("Design", "Watermark", "CONFIDENTIAL 1") or rib("Design", "Watermark", "Confidential 1"); yield 1.0
    shot("w3_watermark")
    rib("Design", "Page Color"); yield 0.6
    K("Escape")

def inserts():
    fresh(); yield 0.3
    T("Text before picture. "); yield 0.3
    from PIL import Image as _I
    _I.new("RGB", (400, 300), (60, 120, 200)).save("/tmp/w3pic.png")
    os.chmod("/tmp/w3pic.png", 0o666)
    win.actions.cmd(".uno:InsertGraphic", {"FileName": "file:///tmp/w3pic.png", "AsLink": False}) if False else None
    try:
        from folio import drawing as DR
        docapi.insert_picture(M(), "/tmp/w3pic.png")
    except Exception as e:
        note("insert picture api", e)
    yield 1.2
    g = M().getGraphicObjects()
    check("picture inserted", g.getCount() == 1, g.getCount())
    if g.getCount():
        o = g.getByIndex(0)
        note("picture anchor/wrap/size", (o.AnchorType.value, o.TextWrap.value, o.Width, o.Height))
        check("new picture inline (Word default)", o.AnchorType.value == "AS_CHARACTER", o.AnchorType.value)
        check("picture fits within margins", o.Width <= 16510 + 10, o.Width)
    shot("w3_picture")
    rib("Insert", "Text Box", "Simple Text Box"); yield 1.0
    check("text box inserted", M().getTextFrames().getCount() == 1, M().getTextFrames().getCount())
    fresh(); yield 0.3
    rib("Insert", "Page Number", "Bottom of Page") ; yield 1.0
    note("page number menu", [d.get_title() for d in dialogs_open()])
    shot("w3_pagenum")
    close_dialogs(); K("Escape"); yield 0.3

run_scenarios(tables, references, review, layout, inserts)
