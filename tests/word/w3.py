exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())

def table_editing():
    fresh(); yield 0.3
    T("Before"); K("Return"); yield 0.3
    win.actions.cmd(".uno:InsertTable", {"Columns": 3, "Rows": 2}) ; yield 1.0
    check("insert 3x2 table", len(tables()) == 1 and len(tables()[0]) == 2 and len(tables()[0][0]) == 3, tables())
    if not tables(): return
    T("a"); K("Tab"); T("b"); K("Tab"); T("c"); K("Tab"); T("d"); yield 0.6
    check("Tab moves to next cell", cell("B1") == "b" and cell("A2") == "d", [cell(n) for n in ("A1","B1","C1","A2")])
    K("shift+Tab"); yield 0.3
    note("shift+tab selects previous cell?", repr(sel()))
    K("ctrl+End"); yield 0.3
    # last cell -> Tab adds row
    cell_rng("C2").caret_to_end(); yield 0.3
    K("Tab"); yield 0.6
    check("Tab in last cell adds a row", len(tables()[0]) == 3, len(tables()[0]))
    T("x"); K("Return"); T("y"); yield 0.5
    check("Enter in cell = new paragraph in cell", "\n" in cell("A3"), repr(cell("A3")))
    # ctrl+tab inserts tab char in cell
    K("ctrl+Tab"); yield 0.3
    check("ctrl+Tab inserts tab in cell", "\t" in cell("A3"), repr(cell("A3")))
    # alt+shift+up moves row up
    K("alt+shift+Up"); yield 0.5
    note("alt+shift+up row move", [cell("A%d" % i) for i in (1, 2, 3)])
    check("alt+shift+Up moves table row up", cell("A2").lower().startswith("x"), [cell("A%d" % i) for i in (1, 2, 3)])
    shot("w3_table")
    # select whole table and press Backspace -> deletes table (Word)
    cell_rng("A1").caret_to_start()
    K("ctrl+a"); yield 0.3
    note("ctrl+a in table selects", repr(sel())[:40])
    # table select via Layout > Select > Select Table then Backspace
    rib("Table Layout", "Select", "Select Table"); yield 0.6
    K("BackSpace"); yield 0.6
    check("Select Table + Backspace deletes table", len(tables()) == 0, len(tables()))
    # Enter at start of first cell of table at doc start inserts paragraph before table
    fresh(); yield 0.3
    win.actions.cmd(".uno:InsertTable", {"Columns": 2, "Rows": 2}); yield 0.8
    caret_start(); yield 0.2
    K("Return"); yield 0.5
    check("Enter at start of table at top inserts paragraph above", blocks()[0][0] == "p", [b[0] for b in blocks()])

def references():
    fresh(); yield 0.3
    for i, h in enumerate(("Intro", "Methods", "Results")):
        T(h); K("ctrl+alt+1"); K("Return"); T("Body text %d." % i); K("Return"); yield 0.3
    yield 0.5
    caret_start(); yield 0.2
    K("Return"); K("ctrl+Home"); yield 0.3
    rib("References", "Table of Contents", "Automatic Table 1") or rib("References", "Table of Contents", "Automatic Table"); yield 1.5
    check("insert TOC", len(tocs()) == 1, len(tocs()))
    if tocs():
        s = tocs()[0]
        check("TOC lists headings", all(h in s for h in ("Intro", "Methods", "Results")), repr(s[:120]))
        # rename a heading then update
        type_at(find_all("Results")[-1], "Findings")
        rib("References", "Update Table"); yield 1.5
        for d in dialogs_open(): note("update dialog", d.get_title())
        respond("Update", Gtk.ResponseType.OK); yield 1.0
        s = tocs()[0]
        check("Update Table refreshes TOC", "Findings" in s, repr(s[:120]))
        shot("w3_toc")
    # footnotes
    K("ctrl+End"); T("Claim"); K("ctrl+alt+f"); yield 1.0
    T("Footnote text."); yield 0.4
    check("footnote inserted and typing goes into it", notes() == 1 and "Footnote text" in caret_para_text(), (notes(), caret_para_text()))
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
    check("ctrl+shift+e turns on Track Changes", E.ed.track_changes(), E.ed.track_changes())
    K("ctrl+Home"); T("New "); yield 0.4
    K("End"); K("BackSpace"); yield 0.4
    n = len(changes())
    check("tracked insertion + deletion recorded", n >= 2, changes())
    shot("w3_track")
    rib("Review", "Accept", "Accept All Changes"); yield 0.8
    n = len(changes())
    check("Accept All Changes clears redlines", n == 0, changes())
    K("ctrl+shift+e"); yield 0.3
    # comments
    find("Original").select(); yield 0.3
    rib("Review", "New Comment"); yield 1.0
    T("My comment"); K("ctrl+Return"); yield 1.2
    cs = comments()
    check("comment created with text", len(cs) == 1 and cs[0]["text"] == "My comment", [c["text"] for c in cs])
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
    focus(); find("This").select(); yield 0.3
    K("shift+F7"); yield 1.2
    shot("w3_thesaurus")
    note("shift+F7 opens", [d.get_title() for d in dialogs_open()])
    close_dialogs(); yield 0.3

def layout():
    fresh(); yield 0.3
    T("Page one text."); yield 0.3
    rib("Layout", "Orientation", "Landscape"); yield 0.8
    ps = page_setup()
    check("Orientation Landscape", ps["width"] > ps["height"], ps)
    rib("Layout", "Orientation", "Portrait"); yield 0.6
    rib("Layout", "Margins", "Narrow"); yield 0.6
    ps = page_setup()
    check("Margins Narrow (1.27cm = 720 twips)", abs(ps["left"] - 720) < 12, (ps["left"], ps["top"]))
    rib("Layout", "Columns", "Two"); yield 0.6
    sec = E.ed.current_section()
    check("Columns Two", page_setup(sec)["cols"] == 2, page_setup(sec))
    rib("Layout", "Columns", "One"); yield 0.5
    K("End"); rib("Layout", "Breaks", "Next Page"); yield 0.8
    T("Section two"); yield 0.3
    rib("Layout", "Orientation", "Landscape"); yield 0.8
    n = page_setup()["section_count"]
    p1 = page_setup(0)["width"] > page_setup(0)["height"]
    p2 = page_setup(n - 1)["width"] > page_setup(n - 1)["height"]
    note("sections", n)
    check("section-level orientation (page 1 portrait, page 2 landscape)", (not p1) and p2, (p1, p2))
    shot("w3_sections")
    rib("Design", "Watermark", "CONFIDENTIAL"); yield 1.0
    check("watermark added", E.ed.has_watermark())
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
    insert_picture("/tmp/w3pic.png")
    yield 1.2
    g = objects("Picture")
    check("picture inserted", len(g) == 1, objects())
    if g:
        o = object_info(g[0][0])
        note("picture anchor/wrap/size", o)
        check("new picture inline (Word default)", o["inline"], o)
        check("picture fits within margins", o["w"] <= 6.5 * 72 + 0.5, o["w"])
    shot("w3_picture")
    rib("Insert", "Text Box", "Simple Text Box"); yield 1.0
    check("text box inserted", len([o for o in objects() if o[1].startswith("Text Box")]) == 1, objects())
    fresh(); yield 0.3
    rib("Insert", "Page Number", "Bottom of Page") ; yield 1.0
    note("page number menu", [d.get_title() for d in dialogs_open()])
    shot("w3_pagenum")
    close_dialogs(); K("Escape"); yield 0.3

run_scenarios(table_editing, references, review, layout, inserts)
