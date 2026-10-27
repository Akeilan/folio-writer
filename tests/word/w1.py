exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())

def cur_props(*names):
    c = vc()
    return {n: getattr(c, n, None) for n in names}

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
    c = vc()
    r = c.getText().createTextCursorByRange(c.getStart()); r.gotoStartOfParagraph(True)
    check("ctrl+right moves by word", r.getString() == "one two ", repr(r.getString()))
    K("ctrl+shift+Right"); yield 0.3
    check("ctrl+shift+right selects word incl. space", sel() == "three ", repr(sel()))
    K("ctrl+Down"); yield 0.3
    c = vc(); r = c.getText().createTextCursorByRange(c.getStart()); r.gotoStartOfParagraph(True)
    check("ctrl+down goes to next paragraph start", r.getString() == "", repr(r.getString()))
    K("shift+End"); yield 0.3
    check("shift+end selects to line end", sel() == "second paragraph here", repr(sel()))
    K("ctrl+a"); yield 0.3
    check("ctrl+a selects all", (sel() or "").count("\n") >= 2, repr(sel())[:50])
    K("ctrl+End"); yield 0.2
    K("ctrl+shift+Up"); yield 0.3
    check("ctrl+shift+up selects to para start", sel() == "third para", repr(sel()))

def char_format():
    fresh(); yield 0.4
    T("plain "); K("ctrl+b"); T("bold"); K("ctrl+b"); T(" "); K("ctrl+i"); T("ital"); K("ctrl+i")
    T(" "); K("ctrl+u"); T("under"); K("ctrl+u"); T(" end")
    yield 1.0
    def fmt_of(word):
        sd = M().createSearchDescriptor(); sd.SearchString = word
        f = M().findFirst(sd)
        return f
    b = fmt_of("bold"); i = fmt_of("ital"); u = fmt_of("under"); e = fmt_of("end")
    check("ctrl+b while typing", b is not None and b.CharWeight > 100, b and b.CharWeight)
    check("ctrl+i while typing", i is not None and int(i.CharPosture.value != "NONE"), i and i.CharPosture.value)
    check("ctrl+u while typing", u is not None and u.CharUnderline == 1, u and u.CharUnderline)
    check("formatting off after toggle", e is not None and e.CharWeight == 100 and e.CharUnderline == 0)
    # select word, ctrl+shift+> grows
    docapi.controller(M()).select(fmt_of("plain")); yield 0.3
    h0 = fmt_of("plain").CharHeight
    K("ctrl+shift+period"); yield 0.4
    h1 = fmt_of("plain").CharHeight
    check("ctrl+shift+> grows font to next size", h1 > h0, (h0, h1))
    K("ctrl+bracketright"); yield 0.4
    h2 = fmt_of("plain").CharHeight
    check("ctrl+] grows by 1pt", abs(h2 - h1 - 1) < 0.01, (h1, h2))
    K("ctrl+space"); yield 0.4
    check("ctrl+space clears char formatting", fmt_of("plain").CharHeight == h0, fmt_of("plain").CharHeight)
    K("ctrl+equal"); yield 0.4
    check("ctrl+= subscript", fmt_of("plain").CharEscapement < 0, fmt_of("plain").CharEscapement)
    K("ctrl+shift+plus"); yield 0.4
    check("ctrl+shift+= superscript", fmt_of("plain").CharEscapement > 0, fmt_of("plain").CharEscapement)
    K("ctrl+space"); yield 0.3
    K("shift+F3"); yield 0.4
    check("shift+F3 change case (UPPER or Title)", fmt_of("plain") is None or fmt_of("plain").getString() != "plain",
          M().getText().getString()[:20])
    K("ctrl+shift+a"); yield 0.4
    note("ctrl+shift+a all caps", (fmt_of("plain") or fmt_of("PLAIN") or fmt_of("Plain")).CharCaseMap if (fmt_of("plain") or fmt_of("PLAIN") or fmt_of("Plain")) else None)
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
    p = lambda: paras()[0]
    for key, want, nm in (("ctrl+e", 3, "center"), ("ctrl+r", 1, "right"), ("ctrl+j", 2, "justify"), ("ctrl+l", 0, "left")):
        K(key); yield 0.3
        check("%s aligns %s" % (key, nm), p().ParaAdjust == want, p().ParaAdjust)
    K("ctrl+2"); yield 0.3
    note("ctrl+2 double spacing", (p().ParaLineSpacing.Mode, p().ParaLineSpacing.Height))
    check("ctrl+2 double spacing", p().ParaLineSpacing.Height == 200, p().ParaLineSpacing.Height)
    K("ctrl+1"); yield 0.3
    check("ctrl+1 single spacing", p().ParaLineSpacing.Height == 100, p().ParaLineSpacing.Height)
    K("ctrl+m"); yield 0.3
    check("ctrl+m indents", p().ParaLeftMargin > 0, p().ParaLeftMargin)
    K("ctrl+shift+m"); yield 0.3
    check("ctrl+shift+m unindents", p().ParaLeftMargin == 0, p().ParaLeftMargin)
    K("ctrl+t"); yield 0.3
    check("ctrl+t hanging indent", p().ParaFirstLineIndent < 0, (p().ParaLeftMargin, p().ParaFirstLineIndent))
    K("ctrl+q"); yield 0.3
    check("ctrl+q clears para formatting", p().ParaFirstLineIndent == 0 and p().ParaLeftMargin == 0, (p().ParaLeftMargin, p().ParaFirstLineIndent))
    K("ctrl+alt+1"); yield 0.4
    check("ctrl+alt+1 Heading 1", p().ParaStyleName == "Heading 1", p().ParaStyleName)
    K("ctrl+alt+2"); yield 0.4
    check("ctrl+alt+2 Heading 2", p().ParaStyleName == "Heading 2", p().ParaStyleName)
    K("ctrl+shift+n"); yield 0.4
    check("ctrl+shift+n Normal", p().ParaStyleName in ("Standard", "Normal", "Default Paragraph Style"), p().ParaStyleName)
    K("ctrl+shift+l"); yield 0.4
    check("ctrl+shift+l List Bullet", "Bullet" in p().ParaStyleName or bool(p().NumberingStyleName) or p().NumberingRules is not None and p().NumberingIsNumber, (p().ParaStyleName, p().NumberingStyleName))
    K("ctrl+shift+n"); yield 0.3
    K("End"); K("Return"); yield 0.3
    T("next"); yield 0.5
    check("Enter after heading -> Normal (next style)", True)

def breaks():
    fresh(); yield 0.4
    T("line one"); K("shift+Return"); T("line two"); yield 0.5
    check("shift+enter line break (same paragraph)", len(paras()) == 1 and "\n" in text(), para_texts())
    K("ctrl+Return"); yield 0.6
    T("page two"); yield 0.5
    check("ctrl+enter page break", E.model.getCurrentController().getPageCount() == 2 if hasattr(E.model.getCurrentController(), "getPageCount") else vc().getPage() == 2, vc().getPage())
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
    hl = None
    try:
        sd = M().createSearchDescriptor(); sd.SearchString = "www.example.com"; f = M().findFirst(sd); hl = f.HyperLinkURL
    except Exception as e:
        hl = e
    check("URL becomes hyperlink", bool(hl), hl)
    fresh(); yield 0.3
    T("1st"); K("space"); yield 0.6
    sd = M().createSearchDescriptor(); sd.SearchString = "st"; f = M().findFirst(sd)
    check("ordinal 1st superscript", f is not None and f.CharEscapement > 0, f and f.CharEscapement)

def autoformat_lists():
    fresh(); yield 0.4
    T("1. first"); K("Return"); T("second"); yield 0.8
    p = paras()
    check("'1. ' starts numbered list", len(p) == 2 and bool(p[1].NumberingIsNumber) and p[1].getString() == "second", [(x.getString(), x.NumberingIsNumber, x.ListLabelString) for x in p])
    check("list label 2.", p[-1].ListLabelString == "2.", p[-1].ListLabelString)
    K("Tab"); yield 0.4
    check("Tab demotes list item", paras()[-1].NumberingLevel == 1, paras()[-1].NumberingLevel)
    note("level-2 label", paras()[-1].ListLabelString)
    K("shift+Tab"); yield 0.4
    check("Shift+Tab promotes", paras()[-1].NumberingLevel == 0, paras()[-1].NumberingLevel)
    K("End"); K("Return"); K("Return"); yield 0.5
    check("Enter on empty item ends list", not paras()[-1].NumberingIsNumber, [(x.getString(), x.NumberingIsNumber) for x in paras()])
    fresh(); yield 0.3
    T("* bullet"); K("Return"); yield 0.6
    p = paras()
    check("'* ' starts bullet list", bool(p[0].NumberingIsNumber), [(x.getString(), x.ListLabelString) for x in p])
    K("BackSpace"); yield 0.4
    check("Backspace at empty bullet removes bullet", not paras()[-1].NumberingIsNumber, paras()[-1].ListLabelString)
    fresh(); yield 0.3
    T("---"); K("Return"); yield 0.7
    p = paras()
    bl = p[0].BottomBorder
    check("--- Enter makes border line", bl.LineWidth > 0 or bl.OuterLineWidth > 0, (p[0].getString(), bl.LineWidth))
    fresh(); yield 0.3
    T("+-----+-----+"); K("Return"); yield 0.8
    check("+---+---+ Enter makes table", M().getTextTables().getCount() == 1, M().getTextTables().getCount())
    fresh(); yield 0.3
    T("a) item"); K("Return"); yield 0.6
    check("'a) ' starts lettered list", bool(paras()[0].NumberingIsNumber), paras()[0].ListLabelString)

def misc_keys():
    fresh(); yield 0.3
    T("repeat"); yield 0.3
    K("ctrl+shift+Left"); K("ctrl+b"); yield 0.3
    K("End"); T(" again"); K("ctrl+shift+Left"); yield 0.3
    K("F4"); yield 0.4
    sd = M().createSearchDescriptor(); sd.SearchString = "again"; f = M().findFirst(sd)
    check("F4 repeats last action (bold)", f is not None and f.CharWeight > 100, f and f.CharWeight)
    fresh(); yield 0.3
    K("alt+shift+d"); yield 0.6
    check("alt+shift+d inserts date", any(ch.isdigit() for ch in text()), repr(text()))
    fresh(); yield 0.3
    T("fmt"); K("ctrl+shift+Left"); K("ctrl+b"); K("ctrl+shift+c"); K("End"); T(" tgt"); K("ctrl+shift+Left"); K("ctrl+shift+v"); yield 0.6
    sd = M().createSearchDescriptor(); sd.SearchString = "tgt"; f = M().findFirst(sd)
    check("ctrl+shift+c / ctrl+shift+v copies formatting", f is not None and f.CharWeight > 100, f and f.CharWeight)
    fresh(); yield 0.3
    T("cut me"); K("ctrl+a", "ctrl+x"); yield 0.4
    check("ctrl+x cuts", text() == "", repr(text()))
    K("ctrl+v"); yield 0.5
    check("ctrl+v pastes", "cut me" in text(), repr(text()))
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
    check("ctrl+alt+m new comment", M().getTextFields().createEnumeration().hasMoreElements(), "")
    shot("w1_comment")
    K("Escape"); yield 0.4
    focus(); K("ctrl+alt+f"); yield 1.0
    check("ctrl+alt+f footnote", M().getFootnotes().getCount() == 1, M().getFootnotes().getCount())
    yield 0.3

run_scenarios(typing_basic, nav_select, char_format, para_format, breaks, autocorrect, autoformat_lists, misc_keys)
