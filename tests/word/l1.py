exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
def styles():
    fresh(); yield 0.3
    T("Preview me please"); yield 0.5
    E.ed.mark_saved()
    undo0 = undo_titles()
    tiles = find_widget(win.ribbon, lambda w: isinstance(w, Gtk.Button) and getattr(w, "style_name", "") == "Heading 1")
    X("mousemove", *widget_center(tiles[0])); yield 1.0
    check("hovering Heading 1 previews it", style_of(0) == "Heading 1", style_of(0))
    shot("l1_hover")
    X("mousemove", 700, 700); yield 0.8
    check("moving away restores", style_of(0) == "Normal", style_of(0))
    check("undo list untouched", undo_titles() == undo0, undo_titles()[:3])
    check("document not marked changed", not modified(), modified())
    X("mousemove", *widget_center(tiles[0])); yield 1.0
    X("click", 1); yield 1.0
    X("mousemove", 700, 700); yield 0.8
    check("clicking applies for real", style_of(0) == "Heading 1", style_of(0))
    K("ctrl+z"); yield 0.8
    check("one undo removes the applied style", style_of(0) == "Normal", style_of(0))
def colors():
    fresh(); yield 0.3
    T("colour word"); K("ctrl+shift+Left"); yield 0.4
    from folio import ribbon_defs as RD, livepreview as LP
    box = RD.color_palette(lambda c: None, preview=(win, lambda c: LP.char_prop(CharColor=c)))
    tw = Gtk.Window(); tw.move(1300, 100); tw.add(box); tw.show_all(); yield 1.0
    sw = find_widget(box, lambda x: isinstance(x, Gtk.Button) and "folio-swatch" in x.get_style_context().list_classes())
    X("mousemove", *widget_center(sw[-1])); yield 1.0
    check("hovering a colour previews it", find("word").run()["color"] not in (-1,), find("word").run()["color"])
    X("mousemove", 700, 700); yield 0.8
    check("colour preview taken back", find("word").run()["color"] == -1, find("word").run()["color"])
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
        check("highlighting a font previews it", find("word").run()["font"] == "Liberation Serif", find("word").run()["font"])
        shot("l1_font")
    fc.popdown(); yield 0.8
    check("closing the list restores", find("word").run()["font"] != "Liberation Serif", find("word").run()["font"])
run_scenarios(colors)
