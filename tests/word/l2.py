exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
sb = win.search_box
def d():
    for q, want in (("insert table", "Table"), ("page num", "Page Number"), ("landscape", "Orientation: Landscape"),
                    ("word count", "Word Count"), ("tabel", "Table"), ("track changes", "Track Changes"),
                    ("bold", "Bold"), ("margins narrow", "Margins: Narrow")):
        hits = [d for d, t, fn in sb.find(q)]
        check("search %r suggests %r" % (q, want), any(h.startswith(want) for h in hits[:3]), hits[:5])
    fresh(); yield 0.3
    T("x"); yield 0.2
    win.search.grab_focus(); yield 0.3
    T("insert tab"); yield 1.0
    shot("l2_suggest")
    check("suggestions show as you type", sb.pop is not None and sb.pop.get_visible() and len(sb.rows) > 2, len(sb.rows))
    K("Return"); yield 1.5
    note("after Enter", ([d.get_title() for d in dialogs_open()], M().getTextTables().getCount(), len(popups())))
    close_dialogs(); K("Escape"); yield 0.5
    win.search.grab_focus(); yield 0.6
    shot("l2_recent")
    check("recently used actions offered", sb.pop is not None and sb.pop.get_visible() and len(sb.rows) >= 1, len(sb.rows))
    K("Escape"); yield 0.3
run_scenarios(d)
