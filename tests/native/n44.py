import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
# 2.33.2 (W3-13): fonts other than the theme fonts. The Font box lists every installed
# font under All Fonts, and picking one (from the list or by typing its name) applies it.


def menu_of(fc):
    for w in Gtk.Window.list_toplevels():
        for m in find_widget(w, lambda x: isinstance(x, Gtk.Menu)):
            if m.get_attach_widget() is fc:
                return m


def pick():
    yield 2.0
    fresh(); yield 0.3
    focus()
    T("font word"); K("ctrl+shift+Left"); yield 0.4
    fc = win.font_combo
    model = [r[0] for r in fc.get_model()]
    theme = {fc.theme[0], fc.theme[1]}
    others = model[model.index("All Fonts") + 1:] if "All Fonts" in model else []
    check("All Fonts lists the installed fonts", len(others) >= 10, len(others))
    want = next((f for f in ("DejaVu Serif", "Liberation Serif", "Caladea") if f in others and f not in theme),
                next((f for f in others if f not in theme), None))
    check("the Font dialog, mini toolbar and Modify Style get the same list", len(E.fonts()) >= 10, len(E.fonts()))
    check("a font that isn't a theme font is listed", want is not None, others[:5])
    if want is None:
        return
    fc.popup(); yield 1.5
    menu = menu_of(fc)
    items = [c for c in menu.get_children() if isinstance(c, Gtk.MenuItem)] if menu else []
    target = items[model.index(want)] if len(items) > model.index(want) else None
    check("the open list has the font", target is not None, len(items))
    if target is None:
        fc.popdown(); return
    menu.select_item(target); yield 0.6
    target.activate(); yield 0.6
    if fc.get_property("popup-shown"):
        fc.popdown()
    yield 0.6
    shot("n44_font_list")
    check("picking it from the list applies it", find("word").run()["font"] == want, find("word").run()["font"])
    check("the box shows it", fc.get_child().get_text() == want, fc.get_child().get_text())
    check("it is now a recent font", want in win.app.settings.get("recent_fonts", []))
    # typing a name in the box
    second = next((f for f in others if f not in theme and f != want), None)
    focus(); yield 0.2
    K("ctrl+a"); yield 0.2
    fc.press(); yield 0.4                   # what the KeyTip (Alt, H, F, F) does
    T(second); yield 0.3
    K("Return"); yield 1.0
    check("typing a font name applies it", find("font").run()["font"] == second, (second, find("font").run()["font"]))
    shot("n44_font_typed")
    E.ed.mark_saved()


run_scenarios(pick)
