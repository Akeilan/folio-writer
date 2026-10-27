exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
def styles():
    fresh(); yield 0.3
    T("Preview me please"); yield 0.5
    M().setModified(False)
    undo0 = list(M().getUndoManager().getAllUndoActionTitles())
    tiles = find_widget(win.ribbon, lambda w: isinstance(w, Gtk.Button) and getattr(w, "style_name", "") == "Heading 1")
    X("mousemove", *widget_center(tiles[0])); yield 1.0
    check("hovering Heading 1 previews it", paras()[0].ParaStyleName == "Heading 1", paras()[0].ParaStyleName)
    shot("l1_hover")
    X("mousemove", 700, 700); yield 0.8
    check("moving away restores", paras()[0].ParaStyleName == "Standard", paras()[0].ParaStyleName)
    check("undo list untouched", list(M().getUndoManager().getAllUndoActionTitles()) == undo0, list(M().getUndoManager().getAllUndoActionTitles())[:3])
    check("document not marked changed", not M().isModified(), M().isModified())
    X("mousemove", *widget_center(tiles[0])); yield 1.0
    X("click", 1); yield 1.0
    X("mousemove", 700, 700); yield 0.8
    check("clicking applies for real", paras()[0].ParaStyleName == "Heading 1", paras()[0].ParaStyleName)
    K("ctrl+z"); yield 0.8
    check("one undo removes the applied style", paras()[0].ParaStyleName == "Standard", paras()[0].ParaStyleName)
def colors():
    fresh(); yield 0.3
    T("colour word"); K("ctrl+shift+Left"); yield 0.4
    from folio import ribbon_defs as RD, livepreview as LP
    box = RD.color_palette(lambda c: None, preview=(win, lambda c: LP.char_prop(CharColor=c)))
    tw = Gtk.Window(); tw.move(1300, 100); tw.add(box); tw.show_all(); yield 1.0
    sw = find_widget(box, lambda x: isinstance(x, Gtk.Button) and "folio-swatch" in x.get_style_context().list_classes())
    X("mousemove", *widget_center(sw[-1])); yield 1.0
    check("hovering a colour previews it", find("word").CharColor not in (-1,), find("word").CharColor)
    X("mousemove", 700, 700); yield 0.8
    check("colour preview taken back", find("word").CharColor == -1, find("word").CharColor)
    tw.destroy()
def fonts():
    fresh(); yield 0.3
    T("font word"); K("ctrl+shift+Left"); yield 0.4
    fc = win.font_combo
    fc.popup(); yield 1.5
    menus = []
    for w in Gtk.Window.list_toplevels():
        menus += [m for m in find_widget(w, lambda x: isinstance(x, Gtk.Menu)) if m.get_attach_widget() is fc]
    items = [c for c in menus[0].get_children() if isinstance(c, Gtk.MenuItem)] if menus else []
    note("font menu items", len(items))
    target = None
    for i, mi in enumerate(items):
        if fc.get_model()[i][0] == "Liberation Serif":
            target = mi
    if target:
        menus[0].select_item(target); yield 1.0
        check("highlighting a font previews it", find("word").CharFontName == "Liberation Serif", find("word").CharFontName)
        shot("l1_font")
    fc.popdown(); yield 0.8
    check("closing the list restores", find("word").CharFontName != "Liberation Serif", find("word").CharFontName)
run_scenarios(colors)
