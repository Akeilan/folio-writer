exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
def word():
    r = find("word")
    if r is None and NATIVE:
        # hidden text isn't found while it's hidden (as in the original): the selection still holds it
        r = docapi.controller(M()).getSelection().getByIndex(0)
    return r
def shortcuts():
    cases = [
        ("ctrl+shift+d", lambda: word().CharUnderline == 2, "double underline"),
        ("ctrl+shift+w", lambda: word().CharWordMode and word().CharUnderline == 1, "word underline"),
        ("ctrl+shift+k", lambda: word().CharCaseMap == 4, "small caps"),
        ("ctrl+shift+h", lambda: word().CharHidden, "hidden"),
    ]
    for key, ok, name in cases:
        fresh(); yield 0.3
        T("a word here"); yield 0.3
        docapi.controller(M()).select(find("word")); yield 0.3
        K(key); yield 0.5
        try: r = ok()
        except Exception as e: r = e
        check("%s %s" % (key, name), r is True, r)
    for key, want, name in (("ctrl+alt+c", "©", "copyright"), ("ctrl+alt+t", "™", "trademark"), ("ctrl+alt+r", "®", "registered"),
                            ("ctrl+alt+period", "…", "ellipsis"), ("ctrl+alt+minus", "—", "em dash"),
                            ("ctrl+shift+space", " ", "nbsp"), ("ctrl+shift+underscore", "‑", "nonbreaking hyphen")):
        fresh(); yield 0.3
        T("x"); K(key); T("y"); yield 0.5
        check("%s inserts %s" % (key, name), want in text(), repr(text()))
    fresh(); yield 0.3
    T("para"); K("ctrl+5"); yield 0.4
    check("ctrl+5 1.5 spacing", paras()[0].ParaLineSpacing.Height == 150, paras()[0].ParaLineSpacing.Height)
    K("ctrl+0"); yield 0.4
    check("ctrl+0 adds 12pt before", paras()[0].ParaTopMargin > 0, paras()[0].ParaTopMargin)
    K("ctrl+shift+asterisk"); yield 0.5
    shot("w7_pilcrow")
    check("ctrl+shift+8 shows formatting marks", win.engine.get(".uno:ControlCodes") == "true", win.engine.get(".uno:ControlCodes"))
    K("ctrl+shift+asterisk"); yield 0.3
    fresh(); yield 0.3
    K("alt+shift+t"); yield 0.5
    check("alt+shift+t inserts time", ":" in text(), repr(text()))
    fresh(); yield 0.3
    K("alt+shift+p"); yield 0.5
    check("alt+shift+p inserts page number", text().strip() == "1", repr(text()))
    fresh(); yield 0.3
    K("ctrl+F9"); yield 0.6
    note("ctrl+F9 field braces", repr(text()))
    fresh(); yield 0.3
    T("Head"); K("ctrl+alt+1"); yield 0.3
    K("alt+shift+Right"); yield 0.4
    check("alt+shift+right demotes heading", paras()[0].ParaStyleName == "Heading 2", paras()[0].ParaStyleName)
    K("alt+shift+Left"); yield 0.4
    check("alt+shift+left promotes heading", paras()[0].ParaStyleName == "Heading 1", paras()[0].ParaStyleName)
    fresh(); yield 0.3
    T("hello"); K("shift+F10"); yield 1.0
    check("shift+F10 opens context menu", len(popups()) > 0, len(popups()))
    shot("w7_shiftf10")
    K("Escape"); yield 0.3
    focus(); K("F5"); yield 1.0
    note("F5", [d.get_title() for d in dialogs_open()])
    close_dialogs(); yield 0.3
    focus(); K("ctrl+shift+f"); yield 0.6
    fw = win.get_focus()
    note("ctrl+shift+f focus", (type(fw).__name__, fw.get_text() if isinstance(fw, Gtk.Entry) else ""))
    check("ctrl+shift+f focuses font box (or opens Font)", isinstance(fw, Gtk.Entry) or bool(dlg("Font")), type(fw).__name__)
    close_dialogs(); focus(); yield 0.3
    K("ctrl+shift+p"); yield 0.6
    fw = win.get_focus()
    check("ctrl+shift+p focuses size box (or opens Font)", isinstance(fw, Gtk.Entry) or bool(dlg("Font")), type(fw).__name__)
    close_dialogs(); focus(); yield 0.3
    K("ctrl+shift+s"); yield 1.0
    note("ctrl+shift+s", ([d.get_title() for d in dialogs_open()], type(win.get_focus()).__name__))
    shot("w7_applystyles")
    close_dialogs(); K("Escape"); focus(); yield 0.3
    K("ctrl+alt+shift+s"); yield 1.0
    shot("w7_stylespane")
    note("styles pane", [type(p).__name__ for p in find_widget(win, lambda w: "Pane" in type(w).__name__ and w.get_visible())])
    K("Escape"); focus(); yield 0.3
    fresh(); yield 0.3
    T("one two three"); K("ctrl+Home"); K("F8"); K("F8"); yield 0.5
    note("F8 x2 selection", repr(sel()))
    K("Escape"); yield 0.3
    fresh(); yield 0.3
    T("first"); K("Return"); T("second"); yield 0.3
    K("ctrl+Home"); yield 0.3
    K("shift+F5"); yield 0.5
    c = vc(); r = c.getText().createTextCursorByRange(c.getStart()); r.gotoStartOfParagraph(True)
    check("shift+F5 returns to last edit", c.getText().createTextCursorByRange(c.getStart()) is not None and r.getString() == "second", repr(r.getString()))
run_scenarios(shortcuts)
