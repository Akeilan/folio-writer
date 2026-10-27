exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
def case():
    fresh(); yield 0.3
    T("hello world"); K("ctrl+shift+Left"); yield 0.3
    out = []
    for i in range(4):
        K("shift+F3"); yield 0.5; out.append(text())
    check("Shift+F3 cycles each press", out == ["hello World", "hello WORLD", "hello world", "hello World"] or len(set(out[:3])) == 3, out)
def altx():
    fresh(); yield 0.3
    T("x00e9"); K("alt+x"); yield 0.5
    check("Alt+X hex->char", text() == "xé", repr(text()))
    K("alt+x"); yield 0.5
    check("Alt+X char->hex", text() == "x00E9", repr(text()))
    fresh(); yield 0.3
    T("U+1F600"); K("alt+x"); yield 0.5
    check("Alt+X U+ form", text() == "😀", repr(text()))
def headings():
    fresh(); yield 0.3
    T("Head"); K("ctrl+alt+1"); yield 0.8
    K("alt+shift+Right"); yield 0.8
    check("Alt+Shift+Right demotes", paras()[0].ParaStyleName == "Heading 2", paras()[0].ParaStyleName)
    K("alt+shift+Left"); yield 0.8
    check("Alt+Shift+Left promotes", paras()[0].ParaStyleName == "Heading 1", paras()[0].ParaStyleName)
def table():
    fresh(); yield 0.3
    win.actions.cmd(".uno:InsertTable", {"Columns": 2, "Rows": 3}); yield 0.8
    t = M().getTextTables().getByIndex(0)
    for n, v in (("A1", "a1"), ("B1", "b1"), ("A2", "a2"), ("B2", "b2"), ("A3", "a3"), ("B3", "b3")):
        t.getCellByName(n).setString(v)
    vc().gotoRange(t.getCellByName("A1").getText().getStart(), False); yield 0.4
    K("Tab"); yield 0.5
    check("Tab selects next cell text", sel() == "b1", repr(sel()))
    K("shift+Tab"); yield 0.5
    check("Shift+Tab selects previous cell text", sel() == "a1", repr(sel()))
    vc().gotoRange(t.getCellByName("A3").getText().getStart(), False); yield 0.4
    K("alt+shift+Up"); yield 0.8
    rows = [[t.getCellByName(c + str(r)).getString() for c in "AB"] for r in (1, 2, 3)]
    check("Alt+Shift+Up moves table row", rows == [["a1", "b1"], ["a3", "b3"], ["a2", "b2"]], rows)
    check("cursor follows the row", vc().Cell is not None and vc().Cell.CellName == "A2", vc().Cell.CellName if vc().Cell else None)
    K("alt+shift+Down"); yield 0.8
    rows = [[t.getCellByName(c + str(r)).getString() for c in "AB"] for r in (1, 2, 3)]
    check("Alt+Shift+Down moves it back", rows == [["a1", "b1"], ["a2", "b2"], ["a3", "b3"]], rows)
    fresh(); yield 0.3
    T("one"); K("Return"); T("two"); yield 0.3
    K("alt+shift+Up"); yield 0.6
    check("Alt+Shift+Up moves paragraph outside tables", para_texts() == ["Two", "One"] or para_texts() == ["two", "One"], para_texts())
def f8():
    fresh(); yield 0.3
    T("One two three. Four five."); K("Return"); T("Next para."); yield 0.4
    K("ctrl+Home"); K("Right"); yield 0.3
    K("F8"); yield 0.4
    check("F8 once: no selection yet", not sel(), repr(sel()))
    K("Right"); K("Right"); yield 0.4
    check("arrows extend in Extend mode", sel() == "ne", repr(sel()))
    K("F8"); yield 0.4; check("F8 x2 word", (sel() or "").strip() == "One", repr(sel()))
    K("F8"); yield 0.4; check("F8 x3 sentence", (sel() or "").strip() == "One two three.", repr(sel()))
    K("F8"); yield 0.4; check("F8 x4 paragraph", (sel() or "").startswith("One two three. Four five."), repr(sel()))
    K("F8"); yield 0.4; check("F8 x5 document", "Next para." in (sel() or ""), repr(sel()))
    K("Escape"); yield 0.3
    K("Right"); yield 0.3; check("Esc ends Extend mode", not sel(), repr(sel()))
def undo():
    fresh(); yield 0.3
    T("one "); yield 0.6; T("two "); yield 0.6
    note("undo titles", list(M().getUndoManager().getAllUndoActionTitles())[:4])
    K("ctrl+z"); yield 0.5
    check("Ctrl+Z undoes word with its space", text() == "One ", repr(text()))
def field():
    fresh(); yield 0.3
    K("ctrl+F9"); yield 1.2
    check("Ctrl+F9 opens Field", bool(dlg("Field")), [d.get_title() for d in dialogs_open()])
    close_dialogs(); yield 0.3
run_scenarios(case, altx, headings, table, f8, undo, field)
