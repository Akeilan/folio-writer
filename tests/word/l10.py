exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
from folio import bordermenu as BM
def borders():
    fresh(); yield 0.3
    win.dialogs._new_table(3, 3); yield 1.0
    K("ctrl+a"); yield 0.3
    t = M().getTextTables().getByIndex(0)
    docapi.controller(M()).select(t.getCellRangeByName("A1:C3")); yield 0.4
    BM.apply(M(), "none"); yield 0.3
    BM.apply(M(), "inside-h"); yield 0.4
    b2 = t.getCellByName("B2")
    check("inside horizontal", b2.TopBorder.OuterLineWidth > 0 and b2.LeftBorder.OuterLineWidth == 0 and t.getCellByName("A1").TopBorder.OuterLineWidth == 0, (b2.TopBorder.OuterLineWidth, b2.LeftBorder.OuterLineWidth))
    shot("l10_tbl")
    fresh(); yield 0.3
    M().getText().setString("a"); yield 0.2
    c = M().getText().createTextCursor(); c.gotoEnd(False)
    M().getText().insertControlCharacter(c, 0, False); M().getText().insertString(c, "b", False)
    K("ctrl+a"); yield 0.4
    BM.apply(M(), "inside-h"); yield 0.4
    ps = paras()
    check("paragraph inside horizontal", ps[0].BottomBorder.OuterLineWidth > 0 and ps[1].BottomBorder.OuterLineWidth == 0, [p.BottomBorder.OuterLineWidth for p in ps])
def menus():
    c = find_control("Layout", "Hyphenation")
    labs = [it[0] for it in c.menu if it and not isinstance(it, Gtk.Widget)]
    check("hyphenation menu", "Manual..." in labs and "Hyphenation Options..." in labs, labs)
    c = find_control("Home", "Borders")
    labs = [it[0] for it in c.menu if it and not isinstance(it, Gtk.Widget)]
    check("borders menu", all(x in labs for x in ("Inside Horizontal Border", "Draw Table", "View Gridlines")), labs)
    GLib.idle_add(lambda: (win.dialogs.hyphenation_options(), False)[1]); yield 1.0
    check("Hyphenation dialog", bool(dlg("Hyphenation")))
    shot("l10_hyph")
    respond("Hyphenation", Gtk.ResponseType.CANCEL); yield 0.4
def fill():
    from folio import filleffects
    GLib.idle_add(lambda: (filleffects.dialog(win), False)[1]); yield 1.0
    check("Fill Effects", bool(dlg("Fill Effects")))
    shot("l10_fill")
    respond("Fill Effects"); yield 1.0
    ps = docapi.page_style(M())
    check("gradient page", ps.FillStyle.value == "GRADIENT", ps.FillStyle.value)
    shot("l10_fillpage")
    docapi.page_color(M(), None); yield 0.4
def review():
    fresh(); yield 0.3
    T("Base text."); yield 0.4
    win.actions.cmd(".uno:TrackChanges"); yield 0.4
    K("End"); T(" Added by me."); yield 0.8
    win.change_bars.refresh(); yield 0.3
    check("has redline", len(win.change_bars.redlines) >= 1, len(win.change_bars.redlines))
    before = text()
    win.set_markup_display("Original"); yield 1.5
    check("Original hides insertion", "Added" not in text(), repr(text()))
    win.set_markup_display("All Markup"); yield 1.5
    check("back to All Markup", text() == before, (repr(text()), repr(before)))
    win.change_bars.refresh(); yield 0.3
    a = win.change_bars.authors()
    note("authors", a)
    if a:
        win.reviewer_filter(a[0], False); yield 0.3
        check("specific people hides bars", not win.change_bars.bars(), "")
        win.all_reviewers(True); yield 0.3
    win.actions.cmd(".uno:TrackChanges"); yield 0.3
run_scenarios(borders, menus, fill, review)
