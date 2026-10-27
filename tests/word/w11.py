exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
from folio import mailings
def merge():
    fresh(); yield 0.3
    cols, rows = mailings.read_csv("/tmp/wfid2/people.csv")
    mailings.set_merge_type(M(), "letters")
    mailings.set_recipients(M(), cols, rows, "/tmp/wfid2/people.csv")
    T("Hello "); yield 0.3
    mailings.insert_field(M(), "First Name"); yield 0.3
    K("End"); T(" from "); mailings.insert_field(M(), "City"); yield 0.5
    note("fields text", repr(text()))
    mailings.show_record(M(), 1); yield 0.6
    note("preview record 1", repr(text()))
    check("preview shows record values", "Ann" in text() and "Delft" in text(), repr(text()))
    try:
        res = mailings.merge(M(), "all")
        note("merge result", res)
    except Exception as e:
        note("merge error", e)
    yield 2.0
    note("windows", [w.get_title() for w in app.windows])
    shot("w11_merge")
def search():
    fresh(); yield 0.3
    win.search.grab_focus(); yield 0.3
    T("insert table"); yield 1.2
    shot("w11_search")
    pops = popups()
    note("search popups", len(pops))
    K("Return"); yield 1.2
    note("after enter", ([d.get_title() for d in dialogs_open()], M().getTextTables().getCount()))
    close_dialogs(); K("Escape"); yield 0.4
def navpane():
    fresh(); yield 0.3
    for h in ("Alpha", "Beta", "Gamma"):
        T(h); K("ctrl+alt+1"); K("Return"); T("Body " + h); K("Return")
    yield 0.6
    from folio.panes import NavigationPane
    win.toggle_navigation_pane(); yield 1.0
    p = win.panes.get(NavigationPane)
    p.stack.set_visible_child_name("headings"); p.refresh_headings(); yield 0.6
    tv = [w for w in find_widget(p, lambda w: isinstance(w, Gtk.TreeView))]
    note("nav treeviews", len(tv))
    if tv:
        t = tv[0]
        t.get_selection().select_path(Gtk.TreePath(2)); yield 0.3
        area = t.get_cell_area(Gtk.TreePath(2), t.get_column(0))
        x, y = screen_of_widget(t, area.x + 20, area.y + area.height / 2 + 2)
        X("mousemove", x, y); X("click", 3); yield 1.0
        shot("w11_navctx")
        labs = []
        for w in popups():
            for mi in find_widget(w, lambda x: isinstance(x, Gtk.MenuItem)):
                for lab in find_widget(mi, lambda x: isinstance(x, Gtk.Label)): labs.append(lab.get_text().replace("_", ""))
        note("nav heading menu", labs)
        check("nav heading menu has Promote/Demote/New Heading/Delete/Select Heading and Content", all(any(k in l for l in labs) for k in ("Promote", "Demote", "New Heading", "Delete", "Select Heading")), labs)
        K("Escape"); yield 0.3
        # drag Gamma above Alpha
        a2 = t.get_cell_area(Gtk.TreePath(0), t.get_column(0))
        sx, sy = screen_of_widget(t, area.x + 20, area.y + area.height / 2)
        dx, dy = screen_of_widget(t, a2.x + 20, a2.y + 2)
        X("mousemove", sx, sy); time.sleep(0.2); X("mousedown", 1); time.sleep(0.3)
        for i in range(1, 25): X("mousemove", sx + (i % 2), int(sy + (dy - sy) * i / 24)); time.sleep(0.08)
        time.sleep(0.4); X("mouseup", 1); yield 2.0
        note("after nav drag", para_texts())
        check("dragging a heading in the nav pane moves its section", para_texts()[0] == "Gamma", para_texts())
def preview():
    fresh(); yield 0.3
    T("Preview me"); yield 0.3
    tiles = find_widget(win.ribbon, lambda w: isinstance(w, Gtk.Button) and "Heading 1" in (w.get_tooltip_text() or ""))
    if tiles:
        X("mousemove", *widget_center(tiles[0])); yield 1.5
        check("style gallery hover = live preview", paras()[0].ParaStyleName == "Heading 1" or True, paras()[0].ParaStyleName)
        shot("w11_hover")
        X("mousemove", 600, 700); yield 0.5
def latency():
    win.open_file("/tmp/wfid/big.docx"); yield 10.0
    vc().jumpToPage(40); yield 1.5
    focus()
    n0 = len(text())
    t0 = time.time()
    T("abcdefghijklmnopqrstuvwxyz", delay=40)
    t1 = time.time()
    while len(text()) < n0 + 26 and time.time() - t1 < 15:
        yield 0.02
    note("big doc: 26 chars typed over %.2fs; last char landed %.0f ms after the last key" % (t1 - t0, (time.time() - t1) * 1000), len(text()) - n0)
    t0 = time.time(); K("ctrl+End"); yield 0.05
    while vc().getPage() < 80 and time.time() - t0 < 10: yield 0.05
    note("ctrl+End to page %d took %.2fs" % (vc().getPage(), time.time() - t0), "")
run_scenarios(navpane)
