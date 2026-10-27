exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
def redlines():
    out = []; en = M().getRedlines().createEnumeration()
    while en.hasMoreElements():
        r = en.nextElement(); out.append((r.RedlineType, r.RedlineAuthor))
    return out
def a():
    fresh(); yield 0.3
    win.actions.cmd(".uno:InsertTable", {"Columns": 2, "Rows": 2}); yield 0.8
    t = M().getTextTables().getByIndex(0)
    rib("Table Layout", "Select", "Select Table"); yield 0.6
    note("sel after Select Table", repr(sel()))
    K("BackSpace"); yield 0.6
    check("Select Table + Backspace deletes table", M().getTextTables().getCount() == 0, M().getTextTables().getCount())
    if M().getTextTables().getCount():
        rib("Table Layout", "Select", "Select Table"); yield 0.6
        K("Delete"); yield 0.6
        note("Delete key on selected table", M().getTextTables().getCount())
def b():
    fresh(); yield 0.3
    for i, h in enumerate(("Intro", "Methods", "Results")):
        T(h); K("ctrl+alt+1"); K("Return"); T("Body text %d." % i); K("Return"); yield 0.3
    K("ctrl+Home"); yield 0.3
    rib("References", "Table of Contents", "Automatic Table 1"); yield 1.5
    idx = M().getDocumentIndexes()
    check("insert TOC", idx.getCount() == 1, idx.getCount())
    shot("w3b_toc")
    if idx.getCount():
        s = idx.getByIndex(0).getAnchor().getString(); note("toc", repr(s))
        sd = M().createSearchDescriptor(); sd.SearchString = "Results"; allr = M().findAll(sd)
        allr.getByIndex(allr.getCount() - 1).setString("Findings"); yield 0.3
        rib("References", "Update Table"); yield 1.5
        note("update dialog", [d.get_title() for d in dialogs_open()])
        respond("Update", Gtk.ResponseType.OK); yield 1.0
        s = idx.getByIndex(0).getAnchor().getString()
        check("Update Table refreshes TOC", "Findings" in s, repr(s))
        # ctrl+click TOC entry jumps
def c():
    fresh(); yield 0.3
    T("Original sentence here."); yield 0.4
    K("ctrl+shift+e"); yield 0.5
    K("ctrl+Home"); T("New "); yield 0.5
    note("redlines after insert", redlines())
    K("ctrl+End"); yield 0.3; K("BackSpace"); yield 0.5
    note("redlines after backspace", redlines())
    docapi.controller(M()).select(find("sentence")); yield 0.3
    K("ctrl+b"); yield 0.5
    note("redlines after bold", redlines())
    shot("w3b_track")
    K("ctrl+shift+e"); yield 0.3
def d():
    fresh(); yield 0.3
    rib("Layout", "Margins", "Narrow"); yield 0.6
    check("Margins Narrow", abs(docapi.page_setup(M())["left"] - 1270) < 20, docapi.page_setup(M())["left"])
    rib("Design", "Watermark", "CONFIDENTIAL"); yield 1.0
    shot("w3b_wm")
    T("Hello"); docapi.controller(M()).select(find("Hello")); yield 0.3
    K("shift+F7"); yield 1.2
    shot("w3b_thes")
    note("after shift+F7", [d.get_title() for d in dialogs_open()])
    close_dialogs(); yield 0.3
    rib("Insert", "Page Number"); yield 1.0
    shot("w3b_pagenum")
    K("Escape"); yield 0.3
run_scenarios(c)
