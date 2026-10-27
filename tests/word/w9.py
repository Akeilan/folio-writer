exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
import importlib
def lists():
    fresh(); yield 0.3
    win.model_call("multilevel_list"); yield 0.6
    T("One\nTwo"); yield 0.8; K("Home"); yield 0.3; K("Tab"); yield 0.6
    p = paras()
    note("multilevel labels", [(x.getString(), x.ListLabelString) for x in p])
    check("multilevel: Tab gives 1.1 style or a.", p[-1].ListLabelString in ("1.1.", "1.1", "a.", "a)"), [x.ListLabelString for x in p])
    fresh(); yield 0.3
    T("1. alpha\nbeta\n"); K("Return"); T("Gap paragraph\n"); yield 0.5
    K("ctrl+shift+n"); yield 0.2
    win.actions.do_numbering(); yield 0.6
    T("gamma"); yield 0.5
    labs = [(x.getString(), x.ListLabelString) for x in paras()]
    note("numbering after a gap", labs)
    # Word asks/continues: new list after a gap restarts at 1 with AutoCorrect bubble; manual Numbering button continues? check context menu items
    GLib.idle_add(lambda: (win.dialogs.context_menu(None), False)[1]); yield 1.0
    labs2 = []
    for w in popups():
        for mi in find_widget(w, lambda x: isinstance(x, Gtk.MenuItem)):
            for lab in find_widget(mi, lambda x: isinstance(x, Gtk.Label)):
                labs2.append(lab.get_text().replace("_", ""))
    note("list context menu", labs2)
    check("list context menu has Restart at 1 / Continue Numbering / Set Numbering Value", any("Restart" in l for l in labs2) and any("Continue" in l for l in labs2) and any("Set Numbering Value" in l for l in labs2), labs2)
    check("list context menu has Adjust List Indents", any("Adjust List Indents" in l for l in labs2), "")
    K("Escape"); yield 0.3
def styles():
    fresh(); yield 0.3
    T("Styled para"); yield 0.3
    gal = [c for c in win.ribbon.controls if type(c).__name__ == "StyleGallery"]
    note("style gallery", type(gal[0]).__name__ if gal else None)
    # right-click on a gallery tile
    tiles = find_widget(win.ribbon, lambda w: isinstance(w, Gtk.Button) and "Heading 1" in (w.get_tooltip_text() or ""))
    if tiles:
        from folio import stylemodify as _sm
        _got = []
        _orig = _sm.context_menu
        _sm.context_menu = lambda *a, **k: (_got.append(_orig(*a, **k)), _got[-1])[1]
        x, y = widget_center(tiles[0]); X("mousemove", x, y); X("click", 3); yield 1.0
        _sm.context_menu = _orig
        labs = []
        for pop in _got:
            for btn in find_widget(pop, lambda x: isinstance(x, Gtk.Button)):
                labs.append((btn.get_label() or "").replace("_", ""))
                for lab in find_widget(btn, lambda x: isinstance(x, Gtk.Label)): labs.append(lab.get_text().replace("_", ""))
        for w in popups():
            for mi in find_widget(w, lambda x: isinstance(x, (Gtk.MenuItem, Gtk.ModelButton, Gtk.Button))):
                t = mi.get_label() if hasattr(mi, "get_label") else ""
                if isinstance(mi, Gtk.ModelButton): t = mi.get_property("text")
                labs.append((t or "").replace("_", ""))
                for lab in find_widget(mi, lambda x: isinstance(x, Gtk.Label)): labs.append(lab.get_text().replace("_", ""))
        note("gallery right-click", labs)
        shot("w9_galctx")
        check("gallery right-click: Update to Match Selection, Modify, Remove from Gallery", any("Update" in l for l in labs) and any("Modify" in l for l in labs) and any("Remove from Style Gallery" in l for l in labs), labs)
        K("Escape"); yield 0.4
    # styles gallery expand: Create a Style / Clear Formatting / Apply Styles
    # style sets in Design tab
    c = find_control("Design", "Themes")
    check("Design > Themes exists", c is not None)
    c2 = [x for x in win.ribbon.controls if getattr(x, "tab_name", "") == "Design" and type(x).__name__ in ("StyleGallery", "Gallery", "DocFormatGallery")]
    note("design controls", [ (type(x).__name__, getattr(x, "label", "")) for x in win.ribbon.controls if getattr(x, "tab_name", "") == "Design"])
def sections():
    fresh(); yield 0.3
    T("Page one"); yield 0.3
    rib("Layout", "Breaks", "Continuous"); yield 0.8
    T("Two columns here and more text to wrap around the columns nicely."); yield 0.3
    rib("Layout", "Columns", "Two"); yield 0.8
    secs = M().getTextSections().getCount()
    note("sections after continuous break + 2 cols", (secs, docapi.page_setup(M())["columns"]))
    shot("w9_cols")
    check("continuous break + Two columns applies to section only", docapi.page_setup(M())["columns"] == 1, docapi.page_setup(M())["columns"])
    fresh(); yield 0.3
    T("first page"); K("ctrl+Return"); T("second page"); yield 0.6
    ps = docapi.page_style(M())
    rib("Insert", "Header", "Blank"); yield 1.0
    T("Header text"); yield 0.5
    win.dialogs.hf_option(("first", None)) if False else None
    note("header text", ps.HeaderText.getString())
    check("header typed", "Header text" in ps.HeaderText.getString(), ps.HeaderText.getString())
    K("Escape"); yield 0.6
    shot("w9_header")
def tables():
    fresh(); yield 0.3
    win.actions.cmd(".uno:InsertTable", {"Columns": 3, "Rows": 3}); yield 0.8
    t = M().getTextTables().getByIndex(0)
    for n, v in zip(t.getCellNames(), "c b a 3 2 1 x y z".split()):
        t.getCellByName(n).setString(v)
    vc().gotoRange(t.getCellByName("A1").getText().getStart(), False); yield 0.3
    # table styles gallery
    c = [x for x in win.ribbon.controls if getattr(x, "tab_name", "") == "Table Design"]
    note("table design controls", [(type(x).__name__, getattr(x, "label", "")) for x in c][:20])
    # formula
    rib("Table Layout", "Formula"); yield 1.2
    note("formula dialog", [d.get_title() for d in dialogs_open()])
    close_dialogs(); yield 0.3
    # convert to text
    rib("Table Layout", "Convert to Text"); yield 1.0
    note("convert to text dlg", [d.get_title() for d in dialogs_open()])
    close_dialogs(); yield 0.3
    # Repeat header rows, AutoFit
    rib("Table Layout", "AutoFit", "AutoFit Contents"); yield 0.8
    note("col widths after autofit", [c.Width if hasattr(c, "Width") else None for c in [t]])
    # table resize handle / move handle: check presence of overlay
    shot("w9_table")
    # Split cells / merge
    docapi.controller(M()).select(t.getCellRangeByName("A1:B1")); yield 0.4
    rib("Table Layout", "Merge Cells"); yield 0.8
    check("merge cells", len(t.getCellNames()) == 8, len(t.getCellNames()))
    # delete row via Backspace on selected row? Word: select row + Backspace deletes row
def refs():
    fresh(); yield 0.3
    T("Text needing a citation"); yield 0.3
    c = find_control("References", "Insert Citation")
    check("Insert Citation button", c is not None)
    c = find_control("References", "Style")
    note("citation style control", type(c).__name__ if c else None)
    rib("References", "Insert Endnote"); yield 1.0
    T("Endnote text"); yield 0.4
    check("endnote", M().getEndnotes().getCount() == 1, M().getEndnotes().getCount())
    focus(); K("ctrl+End"); yield 0.3
    rib("References", "Footnotes Settings"); yield 1.2
    note("footnote dialog", [d.get_title() for d in dialogs_open()])
    close_dialogs(); yield 0.3
def review():
    fresh(); yield 0.3
    T("Review this text please."); yield 0.3
    docapi.controller(M()).select(find("Review")); yield 0.3
    rib("Review", "New Comment"); yield 1.0
    T("first"); K("ctrl+Return"); yield 1.0
    shot("w9_comment")
    cards = list(win.comments.cards.values()) if hasattr(win.comments, "cards") else []
    labs = [l.get_text() for c in cards for l in find_widget(c, lambda w: isinstance(w, Gtk.Label))]
    btns = [b.get_label() for c in cards for b in find_widget(c, lambda w: isinstance(w, Gtk.Button))]
    note("comment card", (labs, btns))
    check("comment card has Reply, Resolve", any("Reply" in (b or "") for b in btns) and any("Resolve" in (b or "") for b in btns), btns)
    # display for review modes
    mc = getattr(win, "markup_choice", None)
    if mc is not None:
        items = [r[0] for r in mc.get_model()]
        check("Display for Review has 4 modes", set(["Simple Markup", "All Markup", "No Markup", "Original"]) <= set(items), items)
    c = find_control("Review", "Show Markup")
    items = [it[0] for it in (c.menu if isinstance(c.menu, list) else []) if it]
    note("show markup menu", items)
    check("Show Markup has Specific People", any("Specific People" in i for i in items), items)
    c = find_control("Review", "Restrict Editing")
    check("Restrict Editing present", c is not None)
    c = find_control("Review", "Block Authors")
    note("block authors", c is not None)
def insert():
    fresh(); yield 0.3
    for lab in ("SmartArt", "Chart", "Icons", "Screenshot", "Shapes", "Cover Page", "Text Box", "WordArt", "Signature Line", "Object", "Equation", "Symbol", "Bookmark", "Cross-reference", "Quick Parts", "Drop Cap", "Date & Time", "Header", "Footer", "Comment", "Table", "Pictures", "Blank Page", "Page Break", "Link", "3D Models", "Online Video", "Add-ins"):
        c = find_control("Insert", lab)
        if c is None:
            note("Insert tab lacks", lab)
    rib("Insert", "Chart"); yield 1.5
    note("chart dialog", [d.get_title() for d in dialogs_open()])
    shot("w9_chart")
    close_dialogs(); yield 0.4
    rib("Insert", "SmartArt"); yield 1.5
    note("smartart dialog", [d.get_title() for d in dialogs_open()])
    shot("w9_smartart")
    close_dialogs(); yield 0.4
    rib("Insert", "Cover Page"); yield 1.0
    shot("w9_cover")
    K("Escape"); yield 0.3
def files():
    fresh(); yield 0.3
    T("Export me"); yield 0.3
    win.show_backstage("home"); yield 1.2
    shot("w9_bs_home")
    win.show_backstage("new"); yield 1.2
    shot("w9_bs_new")
    labs = [l.get_text() for l in find_widget(win.backstage, lambda w: isinstance(w, Gtk.Label) and w.get_mapped())]
    note("new page labels", labs[:40])
    win.show_backstage("info"); yield 1.0
    shot("w9_bs_info")
    win.show_backstage("export"); yield 1.0
    shot("w9_bs_export")
    labs = [l.get_text() for l in find_widget(win.backstage, lambda w: isinstance(w, Gtk.Label) and w.get_mapped())]
    note("export labels", labs[:40])
    win.backstage.close(); yield 0.5
    ok = E.save_as("/tmp/w9.pdf", "pdf", keep=False); yield 1.0
    check("export PDF", ok and os.path.getsize("/tmp/w9.pdf") > 1000, ok)
    for ext in ("odt", "rtf", "txt", "doc", "html"):
        ok = E.save_as("/tmp/w9." + ext, ext, keep=False); yield 0.8
        check("save as %s" % ext, ok and os.path.exists("/tmp/w9." + ext), ok)
run_scenarios(lists, styles, sections, tables, refs, review, insert, files)
