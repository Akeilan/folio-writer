exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
def ps(): return docapi.page_style(M())
def a():
    fresh(); yield 0.3
    T("Some text"); yield 0.3
    docapi.enable_header_footer(M(), "header"); yield 0.5
    win.focus_document(); yield 0.3
    GLib.idle_add(lambda: (win.dialogs.page_setup(2), False)[1]); yield 1.2
    d = dlg("Page Setup")[0]
    shot("l7_layout")
    labs = [w.get_label() for w in find_widget(d, lambda w: isinstance(w, Gtk.Label))]
    for x in ("Section st_art:", "_Vertical alignment:", "Appl_y to:", "From edge:", "_Header:"):
        check("label " + x, x in labs, "")
    chk = {w.get_label(): w for w in find_widget(d, lambda w: isinstance(w, Gtk.CheckButton))}
    chk["Different first _page"].set_active(True)
    chk["Different _odd and even"].set_active(True)
    combos = find_widget(d, lambda w: isinstance(w, Gtk.ComboBoxText))
    note("combos", [c.get_active_text() for c in combos])
    by = {c.get_active_text(): c for c in combos}
    by["Top"].set_active(1)      # vertical center
    by["Normal"].set_active(1)   # mirror margins
    spins = find_widget(d, lambda w: w.__class__.__name__ == "LengthSpin")
    note("spins", len(spins))
    btns = [b.get_label() for b in find_widget(d, lambda w: isinstance(w, Gtk.Button))]
    check("Set As Default button", "Set As De_fault" in btns, btns)
    respond("Page Setup"); yield 1.0
    p = ps()
    check("mirrored", p.PageStyleLayout.value == "MIRRORED", p.PageStyleLayout.value)
    note("vertical center (read)", p.TextVerticalAdjust.value)
    check("different first", p.FirstIsShared is False, p.FirstIsShared)
    check("different odd/even", p.HeaderIsShared is False, p.HeaderIsShared)
    shot("l7_after")
    # Margins menu Mirrored / Normal
    rib("Layout", "Margins", "Normal"); yield 0.6
    check("Normal undoes mirror", ps().PageStyleLayout.value == "ALL", ps().PageStyleLayout.value)
    rib("Layout", "Margins", "Mirrored"); yield 0.6
    check("Mirrored menu", ps().PageStyleLayout.value == "MIRRORED" and ps().LeftMargin == 3175, (ps().PageStyleLayout.value, ps().LeftMargin))
    # save docx keeps mirror + valign
    win.save_to("/tmp/dc/l7.docx"); yield 3.0
    import zipfile
    x = zipfile.ZipFile("/tmp/dc/l7.docx").read("word/settings.xml").decode()
    y = zipfile.ZipFile("/tmp/dc/l7.docx").read("word/document.xml").decode()
    check("docx mirrorMargins", "mirrorMargins" in x, "")
    check("docx vAlign", 'w:vAlign w:val="center"' in y, y[y.find("<w:sectPr"):][:500])
run_scenarios(a)
