exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
def a():
    fresh(); yield 0.3
    T("Some text"); yield 0.3
    E.ed.ensure_header_footer(0, False); E.view.after_edit(); yield 0.5
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
    p = page_setup()
    check("mirrored", E.ed.setting("mirrorMargins"), E.ed.setting("mirrorMargins"))
    check("vertical center", p["v_align"] == "center", p["v_align"])
    check("different first", p["title_pg"], p["title_pg"])
    check("different odd/even", E.ed.setting("evenAndOddHeaders"), E.ed.setting("evenAndOddHeaders"))
    shot("l7_after")
    # Margins menu Mirrored / Normal
    rib("Layout", "Margins", "Normal"); yield 0.6
    check("Normal undoes mirror", not E.ed.setting("mirrorMargins"), E.ed.setting("mirrorMargins"))
    rib("Layout", "Margins", "Mirrored"); yield 0.6
    check("Mirrored menu (inside 1.25 in)", E.ed.setting("mirrorMargins") and page_setup()["left"] == 1800, (E.ed.setting("mirrorMargins"), page_setup()["left"]))
    # save docx keeps mirror + valign
    win.save_to("/tmp/dc/l7.docx"); yield 3.0
    import zipfile
    x = zipfile.ZipFile("/tmp/dc/l7.docx").read("word/settings.xml").decode()
    y = zipfile.ZipFile("/tmp/dc/l7.docx").read("word/document.xml").decode()
    check("docx mirrorMargins", "mirrorMargins" in x, "")
    check("docx vAlign", 'w:vAlign w:val="center"' in y, y[y.find("<w:sectPr"):][:500])
run_scenarios(a)
