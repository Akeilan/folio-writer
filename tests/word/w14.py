import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
def word_xy(word, frac, nth=0):
    r = find(word, nth); r.caret_to_start(); yield 0.3
    x0, y0, w, h = win._follow_rect
    r.caret_to_end(); yield 0.3
    x1 = win._follow_rect[0]
    P["xy"] = doc_screen(x0 + (x1 - x0) * frac, y0 + h / 2)
P = {}
def ac_undo():
    fresh(); yield 0.3
    T("I saw teh "); yield 0.6
    K("ctrl+z"); yield 0.5
    check("Ctrl+Z right after AutoCorrect restores the typed word", "teh" in text(), repr(text()))
    fresh(); yield 0.3
    T("He said \"hi\""); yield 0.5
    K("ctrl+z"); yield 0.5
    check("Ctrl+Z after smart quote restores straight quote", text().endswith('"'), repr(text()))
def smartcut():
    fresh(); yield 0.3
    T("one two three"); yield 0.4
    yield from word_xy("two", 0.5)
    click(*P["xy"], n=2); yield 0.5
    note("double-click selection", repr(sel()))
    K("ctrl+x"); yield 0.6
    check("smart cut leaves single spaces", text() == "One three", repr(text()))
    K("End"); K("space"); K("ctrl+v"); yield 0.8
    check("smart paste adds spacing", text() in ("One three two", "One three two "), repr(text()))
def sticky_painter():
    fresh(); yield 0.3
    T("src a b c"); yield 0.3
    find("src").select(); K("ctrl+b"); yield 0.3
    spots = []
    for w in ("a", "b", "c"):
        yield from word_xy(" %s" % w, 0.8)
        spots.append(P["xy"])
    find("src").caret_to_end(); yield 0.3
    c = find_control("Home", "Format Painter")
    x, y = widget_center(c)
    X("mousemove", x, y); X("click", "--repeat", 2, "--delay", 80, 1); yield 0.6
    note("painter after double-click", (win.painter.active, win.painter.sticky))
    for xy in spots:
        click(*xy); yield 0.8
        note("after click", (win.painter.active, win.painter.sticky, caret(), E.ed.has_format()))
    def last(r):
        return Rng((r.b[0], r.b[1] - 1), r.b).run()["bold"]
    got = [last(find(" %s" % w)) for w in ("a", "b", "c")]
    check("double-clicked Format Painter stays on for several clicks", all(got), got)
    K("Escape"); yield 0.3
def toc_click():
    fresh(); yield 0.3
    T("Intro"); K("ctrl+alt+1"); K("Return"); T("text"); K("ctrl+Return"); T("Second"); K("ctrl+alt+1"); yield 0.6
    K("ctrl+Home"); K("Return"); K("ctrl+Home"); yield 0.3
    rib("References", "Table of Contents", "Automatic Table 1"); yield 1.5
    yield from word_xy("Second", 0.3)
    click(*P["xy"], mods="ctrl"); yield 1.0
    check("Ctrl+click TOC entry jumps to heading", caret_page() == 1 and caret_para_text() == "Second", (caret_page(), caret_para_text()))
def overtype():
    fresh(); yield 0.3
    T("abc"); K("Home"); K("Insert"); T("X"); yield 0.5
    check("Insert key does not turn on overtype (Word default)", text() == "Xabc", repr(text()))
    if text() != "Xabc":
        K("Insert")
def autocorrect_button():
    fresh(); yield 0.3
    T("I saw teh "); yield 0.6
    yield from word_xy("the", 0.5)
    X("mousemove", *P["xy"]); yield 1.2
    shot("w14_acbutton")
    note("popups after hover on corrected word", len(popups()))
def spell_ignore():
    fresh(); yield 0.3
    T("Zorgleflux is odd. Zorgleflux again. "); yield 1.0
    yield from word_xy("Zorgleflux", 0.5)
    click(*P["xy"], button=3); yield 1.0
    items = []
    for w in popups():
        for mi in find_widget(w, lambda x: isinstance(x, Gtk.MenuItem)):
            for lab in find_widget(mi, lambda x: isinstance(x, Gtk.Label)):
                items.append((lab.get_text(), mi))
    ign = [mi for t, mi in items if "Ignore All" in t]
    if ign:
        GLib.idle_add(lambda: (ign[0].activate(), False)[1]); yield 1.2
    shot("w14_ignore")
    sp = E.view.speller
    check("ignored word no longer marked", sp is not None and sp.ignored("Zorgleflux"), sp)
run_scenarios(ac_undo, smartcut, sticky_painter, toc_click, overtype, autocorrect_button, spell_ignore)
