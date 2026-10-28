exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())

def typing_basic():
    fresh(); yield 0.5
    T("Hello world. this is a test")
    yield 1.0
    check("typed text arrives", text().startswith("Hello world."), repr(text()[:60]))
    check("auto-capitalize sentence start (this->This)", "This is a test" in text(), repr(text()))
    K("ctrl+z"); yield 0.5
    note("after ctrl+z", repr(text()))
    K("ctrl+y"); yield 0.5
    note("after ctrl+y", repr(text()))
    K("ctrl+BackSpace"); yield 0.4
    check("ctrl+backspace deletes previous word", text().rstrip().endswith("a") or text().endswith("a "), repr(text()))
    K("Home"); yield 0.2
    K("ctrl+Delete"); yield 0.4
    check("ctrl+delete deletes next word", text().startswith("world"), repr(text()))
    K("ctrl+z", "ctrl+z"); yield 0.4

def nav_select():
    fresh(); yield 0.4
    T("one two three four\nsecond paragraph here\nthird para")
    yield 1.0
    K("ctrl+Home"); yield 0.2
    K("ctrl+Right", "ctrl+Right"); yield 0.3
    check("ctrl+right moves by word", pos().lower() == "one two ", repr(pos()))
    K("ctrl+shift+Right"); yield 0.3
    check("ctrl+shift+right selects word incl. space", sel() == "three ", repr(sel()))
    K("ctrl+Down"); yield 0.3
    check("ctrl+down goes to next paragraph start", pos() == "" and caret_para_text().lower() == "second paragraph here", repr(pos()))
    K("shift+End"); yield 0.3
    check("shift+end selects to line end", (sel() or "").lower() == "second paragraph here", repr(sel()))
    K("ctrl+a"); yield 0.3
    check("ctrl+a selects all", (sel() or "").count("\n") >= 2, repr(sel())[:50])
    K("ctrl+End"); yield 0.2
    K("ctrl+shift+Up"); yield 0.3
    check("ctrl+shift+up selects to para start", (sel() or "").lower() == "third para", repr(sel()))

def char_format():
    fresh(); yield 0.4
    T("plain "); K("ctrl+b"); T("bold"); K("ctrl+b"); T(" "); K("ctrl+i"); T("ital"); K("ctrl+i")
    T(" "); K("ctrl+u"); T("under"); K("ctrl+u"); T(" end")
    yield 1.0
    def fmt_of(word):
        r = find(word)
        return r.run() if r else None
    b = fmt_of("bold"); i = fmt_of("ital"); u = fmt_of("under"); e = fmt_of("end")
    check("ctrl+b while typing", b is not None and b["bold"], b)
    check("ctrl+i while typing", i is not None and i["italic"], i)
    check("ctrl+u while typing", u is not None and u["underline"] == "single", u and u["underline"])
    check("formatting off after toggle", e is not None and not e["bold"] and not e["italic"] and e["underline"] == "none", e)
    # select word, ctrl+shift+> grows
    find("plain").select(); yield 0.3
    h0 = fmt_of("plain")["size"]
    K("ctrl+shift+period"); yield 0.4
    h1 = fmt_of("plain")["size"]
    check("ctrl+shift+> grows font to next size", h1 > h0, (h0, h1))
    K("ctrl+bracketright"); yield 0.4
    h2 = fmt_of("plain")["size"]
    check("ctrl+] grows by 1pt", abs(h2 - h1 - 1) < 0.01, (h1, h2))
    K("ctrl+space"); yield 0.4
    check("ctrl+space clears char formatting", fmt_of("plain")["size"] == h0, fmt_of("plain")["size"])
    K("ctrl+equal"); yield 0.4
    check("ctrl+= subscript", fmt_of("plain")["vert_align"] == "subscript", fmt_of("plain")["vert_align"])
    K("ctrl+shift+plus"); yield 0.4
    check("ctrl+shift+= superscript", fmt_of("plain")["vert_align"] == "superscript", fmt_of("plain")["vert_align"])
    K("ctrl+space"); yield 0.3
    K("shift+F3"); yield 0.4
    check("shift+F3 change case (UPPER or Title)", find("plain", case=True) is None, text()[:20])
    K("ctrl+shift+a"); yield 0.4
    note("ctrl+shift+a all caps", rv()["caps"])
    K("ctrl+d"); yield 1.0
    dlg = [w for w in Gtk.Window.list_toplevels() if w.get_visible() and w is not win and isinstance(w, Gtk.Window) and w.get_title()]
    check("ctrl+d opens Font dialog", any("Font" in (w.get_title() or "") for w in dlg), [w.get_title() for w in dlg])
    for w in dlg:
        if isinstance(w, Gtk.Dialog): w.response(Gtk.ResponseType.CANCEL)
    yield 0.5

def para_format():
    fresh(); yield 0.4
    T("A paragraph for alignment")
    yield 0.6
    p = lambda: pv(0)
    for key, want, nm in (("ctrl+e", "center", "center"), ("ctrl+r", "right", "right"), ("ctrl+j", "both", "justify"), ("ctrl+l", "left", "left")):
        K(key); yield 0.3
        check("%s aligns %s" % (key, nm), p()["align"] == want, p()["align"])
    K("ctrl+2"); yield 0.3
    check("ctrl+2 double spacing", (p()["line"], p()["line_rule"]) == (480, "auto"), (p()["line"], p()["line_rule"]))
    K("ctrl+1"); yield 0.3
    check("ctrl+1 single spacing", (p()["line"], p()["line_rule"]) == (240, "auto"), (p()["line"], p()["line_rule"]))
    K("ctrl+m"); yield 0.3
    check("ctrl+m indents", p()["ind_left"] > 0, p()["ind_left"])
    K("ctrl+shift+m"); yield 0.3
    check("ctrl+shift+m unindents", p()["ind_left"] == 0, p()["ind_left"])
    K("ctrl+t"); yield 0.3
    check("ctrl+t hanging indent", p()["ind_first"] < 0, (p()["ind_left"], p()["ind_first"]))
    K("ctrl+q"); yield 0.3
    check("ctrl+q clears para formatting", p()["ind_first"] == 0 and p()["ind_left"] == 0, (p()["ind_left"], p()["ind_first"]))
    K("ctrl+alt+1"); yield 0.4
    check("ctrl+alt+1 Heading 1", p()["style"] == "Heading 1", p()["style"])
    K("ctrl+alt+2"); yield 0.4
    check("ctrl+alt+2 Heading 2", p()["style"] == "Heading 2", p()["style"])
    K("ctrl+shift+n"); yield 0.4
    check("ctrl+shift+n Normal", p()["style"] == "Normal", p()["style"])
    K("ctrl+shift+l"); yield 0.4
    check("ctrl+shift+l List Bullet", "Bullet" in p()["style"] and is_listed(0), (p()["style"], list_info(0)))
    K("ctrl+shift+n"); yield 0.3
    K("End"); K("Return"); yield 0.3
    T("next"); yield 0.5
    check("Enter after heading -> Normal (next style)", True)

def breaks():
    fresh(); yield 0.4
    T("line one"); K("shift+Return"); T("line two"); yield 0.5
    check("shift+enter line break (same paragraph)", len(blocks()) == 1 and "\n" in text(), para_texts())
    K("ctrl+Return"); yield 0.6
    T("page two"); yield 0.5
    check("ctrl+enter page break", caret_page() == 1, caret_page())
    K("ctrl+shift+Return"); yield 0.5
    note("ctrl+shift+enter column break", para_texts())

def autocorrect():
    fresh(); yield 0.4
    cases = [("teh ", "the "), ("(c) ", "© "), ("i am ", "I am "), ("word -- word ", "–"), ("1st ", "1st"),
             ("\"quoted\" ", "“quoted”"), ("don't ", "don’t"), ("1/2 ", "½"), ("-> ", "→"), (":) ", "☺")]
    for inp, want in cases:
        fresh(); yield 0.3
        T("Start " + inp); yield 0.7
        got = text()
        check("autocorrect %r" % inp.strip(), want in got, repr(got))
    fresh(); yield 0.3
    T("Visit www.example.com "); yield 0.7
    r = find("www.example.com")
    hl = link_here(r) if r else None
    check("URL becomes hyperlink", bool(hl), hl)
    fresh(); yield 0.3
    T("1st"); K("space"); yield 0.6
    f = find("st")
    check("ordinal 1st superscript", f is not None and f.run()["vert_align"] == "superscript", f and f.run()["vert_align"])

def autoformat_lists():
    fresh(); yield 0.4
    T("1. first"); K("Return"); T("second"); yield 0.8
    p = para_texts()
    check("'1. ' starts numbered list", len(p) == 2 and is_listed(1) and p[1] == "second", [(t, list_label(i)) for i, t in enumerate(p)])
    check("list label 2.", list_label(-1) == "2.", list_label(-1))
    K("Home"); K("Tab"); yield 0.4
    check("Tab demotes list item", list_level(-1) == 1, list_level(-1))
    note("level-2 label", list_label(-1))
    K("shift+Tab"); yield 0.4
    check("Shift+Tab promotes", list_level(-1) == 0, list_level(-1))
    K("End"); K("Return"); K("Return"); yield 0.5
    check("Enter on empty item ends list", not is_listed(-1), [(t, is_listed(i)) for i, t in enumerate(para_texts())])
    fresh(); yield 0.3
    T("* bullet"); K("Return"); yield 0.6
    check("'* ' starts bullet list", is_listed(0), [(t, list_label(i)) for i, t in enumerate(para_texts())])
    K("BackSpace"); yield 0.4
    check("Backspace at empty bullet removes bullet", not is_listed(-1), list_label(-1))
    fresh(); yield 0.3
    T("---"); K("Return"); yield 0.7
    bl = border("bottom", 0)
    check("--- Enter makes border line", bool(bl) and bl[1] > 0, (para_texts()[0], bl))
    fresh(); yield 0.3
    T("+-----+-----+"); K("Return"); yield 0.8
    check("+---+---+ Enter makes table", len(tables()) == 1, len(tables()))
    fresh(); yield 0.3
    T("a) item"); K("Return"); yield 0.6
    check("'a) ' starts lettered list", is_listed(0), list_label(0))

def misc_keys():
    fresh(); yield 0.3
    T("repeat"); yield 0.3
    K("ctrl+shift+Left"); K("ctrl+b"); yield 0.3
    K("End"); T(" again"); K("ctrl+shift+Left"); yield 0.3
    K("F4"); yield 0.4
    f = find("again")
    check("F4 repeats last action (bold)", f is not None and f.run()["bold"], f and f.run()["bold"])
    fresh(); yield 0.3
    K("alt+shift+d"); yield 0.6
    check("alt+shift+d inserts date", any(ch.isdigit() for ch in text()), repr(text()))
    fresh(); yield 0.3
    T("fmt"); K("ctrl+shift+Left"); K("ctrl+b"); K("ctrl+shift+c"); K("End"); T(" tgt"); K("ctrl+shift+Left"); K("ctrl+shift+v"); yield 0.6
    f = find("tgt")
    check("ctrl+shift+c / ctrl+shift+v copies formatting", f is not None and f.run()["bold"], f and f.run()["bold"])
    fresh(); yield 0.3
    T("cut me"); K("ctrl+a", "ctrl+x"); yield 0.4
    check("ctrl+x cuts", text() == "", repr(text()))
    K("ctrl+v"); yield 0.5
    check("ctrl+v pastes", "cut me" in text().lower(), repr(text()))
    K("ctrl+alt+v"); yield 1.0
    dlg = [w.get_title() for w in Gtk.Window.list_toplevels() if w.get_visible() and w is not win and w.get_title()]
    check("ctrl+alt+v Paste Special dialog", any("Paste" in t for t in dlg), dlg)
    for w in Gtk.Window.list_toplevels():
        if isinstance(w, Gtk.Dialog) and w.get_visible(): w.response(Gtk.ResponseType.CANCEL)
    yield 0.4
    K("ctrl+f"); yield 0.8
    check("ctrl+f opens navigation pane search", win.search is not None, "")
    shot("w1_ctrlf")
    K("Escape"); yield 0.3
    focus(); K("ctrl+h"); yield 1.0
    dlg = [w.get_title() for w in Gtk.Window.list_toplevels() if w.get_visible() and w is not win and w.get_title()]
    check("ctrl+h Find and Replace", any("Replace" in t for t in dlg), dlg)
    for w in Gtk.Window.list_toplevels():
        if isinstance(w, Gtk.Dialog) and w.get_visible(): w.response(Gtk.ResponseType.CANCEL)
    yield 0.4
    focus(); K("ctrl+k"); yield 1.0
    dlg = [w.get_title() for w in Gtk.Window.list_toplevels() if w.get_visible() and w is not win and w.get_title()]
    check("ctrl+k Insert Hyperlink", any("Link" in t or "Hyperlink" in t for t in dlg), dlg)
    for w in Gtk.Window.list_toplevels():
        if isinstance(w, Gtk.Dialog) and w.get_visible(): w.response(Gtk.ResponseType.CANCEL)
    yield 0.4
    focus(); K("alt+equal"); yield 1.0
    check("alt+= inserts equation", win.eqbar.ed.active, "")
    K("Escape"); yield 0.5
    focus(); K("ctrl+alt+m"); yield 1.0
    T("A note"); K("ctrl+Return"); yield 0.8
    check("ctrl+alt+m new comment", bool(E.ed.comments()), E.ed.comments())
    shot("w1_comment")
    K("Escape"); yield 0.4
    focus(); K("ctrl+alt+f"); yield 1.0
    check("ctrl+alt+f footnote", notes() == 1, notes())
    yield 0.3

run_scenarios(typing_basic, nav_select, char_format, para_format, breaks, autocorrect, autoformat_lists, misc_keys)
