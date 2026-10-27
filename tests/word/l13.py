exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
def fmt():
    fresh(); yield 0.3
    t = M().getText()
    t.setString("Source words")
    c = t.createTextCursor(); c.gotoEnd(False)
    t.insertControlCharacter(c, 0, False); t.insertString(c, "Target words", False); yield 0.4
    p0 = paras()[0]
    c0 = t.createTextCursorByRange(p0.getStart()); c0.gotoEndOfParagraph(True)
    c0.CharWeight = 150.0; c0.CharColor = 0xC00000; c0.CharHeight = 16.0
    p0.ParaAdjust = 3; p0.ParaLeftMargin = 1270
    K("ctrl+Home"); K("Right"); yield 0.4
    K("ctrl+shift+c"); yield 0.5
    K("ctrl+End"); yield 0.4
    K("ctrl+shift+v"); yield 0.8
    p1 = paras()[1]
    c1 = t.createTextCursorByRange(p1.getEnd()); c1.goLeft(3, True)
    check("char formatting pasted", c1.CharWeight == 150.0 and c1.CharColor == 0xC00000 and c1.CharHeight == 16.0, (c1.CharWeight, c1.CharColor, c1.CharHeight))
    check("paragraph formatting pasted", p1.ParaAdjust == 3 and p1.ParaLeftMargin == 1270, (p1.ParaAdjust, p1.ParaLeftMargin))
def hf():
    fresh(); yield 0.3
    T("x"); yield 0.3
    win.run("header"); yield 1.2
    win.select_tab("Header & Footer"); yield 0.5
    sb = win.hf_spins["header_top"]
    sb.set_value(2000); yield 0.8
    ps = docapi.page_style(M())
    check("header from top", abs(ps.TopMargin - 2000) < 20, ps.TopMargin)
    labs = [_clean(getattr(c, "label", "") or "") or (getattr(c, "tooltip_text", "") or "") for c in win.ribbon.controls if getattr(c, "tab_name", "") == "Header & Footer"]
    check("Insert Alignment Tab button", "Insert Alignment Tab" in labs, labs)
    from folio import hfedit
    GLib.idle_add(lambda: (hfedit.alignment_tab_dialog(win), False)[1]); yield 1.0
    check("Alignment Tab dialog", bool(dlg("Alignment Tab")))
    respond("Alignment Tab"); yield 0.8
    h = ps.HeaderText.getString()
    check("tab inserted in header", "\t" in h, repr(h))
    shot("l13_hf")
run_scenarios(fmt, hf)
