exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
def button():
    fresh(); yield 0.3
    T("I saw teh "); yield 1.0
    check("AutoCorrect button appears", win.acwatch.btn.get_visible(), win.acwatch.last)
    shot("l3_button")
    win.acwatch.change_back(); yield 0.6
    check("Change back restores what was typed", "teh" in text(), repr(text()))
    fresh(); yield 0.3
    T("hello there. this is it "); yield 1.0
    note("caps last", win.acwatch.last and (win.acwatch.last["old"], win.acwatch.last["new"], win.acwatch.last["kind"]))
    check("capitalization recorded", win.acwatch.last is not None and win.acwatch.last["kind"] == "caps", "")
    fresh(); yield 0.3
    T("see you monday "); yield 1.0
    check("names of days capitalized", "Monday" in text(), repr(text()))
def tabindent():
    fresh(); yield 0.3
    T("Paragraph text"); K("Home"); yield 0.3
    K("Tab"); yield 0.5
    check("Tab at paragraph start sets first-line indent", paras()[0].ParaFirstLineIndent > 0 and "\t" not in text(), (paras()[0].ParaFirstLineIndent, repr(text())))
    K("BackSpace"); yield 0.5
    check("Backspace removes it", paras()[0].ParaFirstLineIndent == 0 and text() == "Paragraph text", (paras()[0].ParaFirstLineIndent, repr(text())))
    fresh(); yield 0.3
    K("Tab"); T("x"); yield 0.5
    check("Tab in an empty paragraph types a tab", text() == "\tx", repr(text()))
def dialog():
    GLib.idle_add(lambda: (win.dialogs.autocorrect_options(), False)[1]); yield 1.5
    d = dlg("AutoCorrect")
    shot("l3_dialog")
    tabs = []
    for nb in find_widget(d[0], lambda w: isinstance(w, Gtk.Notebook)) if d else []:
        tabs += [nb.get_tab_label(nb.get_nth_page(i)).get_text() for i in range(nb.get_n_pages())]
    check("AutoCorrect dialog has tabs", tabs[:3] == ["AutoCorrect", "Math AutoCorrect", "AutoFormat As You Type"], tabs)
    nb = find_widget(d[0], lambda w: isinstance(w, Gtk.Notebook))[0]
    nb.set_current_page(2); yield 0.6
    shot("l3_dialog2")
    close_dialogs(); yield 0.5
run_scenarios(button, tabindent, dialog)
