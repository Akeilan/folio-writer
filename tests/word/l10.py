import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
from folio import bordermenu as BM
def borders():
    fresh(); yield 0.3
    win.dialogs._new_table(3, 3); yield 1.0
    K("ctrl+a"); yield 0.3
    Rng(cell_rng("A1").a, cell_rng("C3").b).select(); yield 0.4
    BM.apply_win(win, "none"); yield 0.3
    BM.apply_win(win, "inside-h"); yield 0.4
    st = (cell_border("B2", "top"), cell_border("B2", "left"), cell_border("A1", "top"))
    check("inside horizontal", st == (True, False, False), st)
    shot("l10_tbl")
    fresh(); yield 0.3
    set_text("a\nb"); yield 0.2
    K("ctrl+a"); yield 0.4
    BM.apply_win(win, "inside-h"); yield 0.4
    st = [(border("between", i), border("bottom", i)) for i in range(2)]
    check("paragraph inside horizontal", bool(st[0][0]) and not st[0][1] and not st[1][1], st)
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
    pf = E.ed.page_fill()
    check("gradient page", pf is not None and "grad" in pf[0].lower(), pf)
    shot("l10_fillpage")
    E.ed.set_page_color(None); E.view.after_edit(); yield 0.4
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
