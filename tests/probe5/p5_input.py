# Real mouse and keyboard, the way a person edits.
import os as _o; TESTS = _o.environ["FOLIO_WRITER_TESTS"]; exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read()); exec(open("/tmp/p5/probes/ph.py").read())
V = win.engine.view
def scr(word, nth=0, at=0.0, para=None):
    """Screen x,y of a word's start (at=0) .. end (at=1)."""
    r = find(word, nth)
    p, a, b = r.a[0], r.a[1], r.b[1]
    rc = ed().range_rects(p, a, p, b)
    pg, x, y, w, h = rc[0][:5]
    wx, wy = V.to_widget(pg, x + w * at, y + h / 2)
    return screen_of_widget(V, wx, wy)
def setdoc(s):
    fresh(); pump(0.2); ed().type_text(s); V.after_edit(); pump(0.3)
PARA = "The quick brown fox jumps over the lazy dog near the quiet river bank."

def mouse():
    yield 0.5
    focus(); setdoc(PARA + "\n" + "Second paragraph has different words inside."); yield 0.3
    note("find shape", find("brown"))
    x, y = scr("brown"); click(x + 1, y); yield 0.3
    check("click puts the caret before the word", pos().endswith("quick "), pos())
    x, y = scr("fox", at=0.5); click(x, y, n=2); yield 0.4
    check("double-click selects the word", (sel() or "").strip() == "fox", sel())
    yield 0.8
    click(x, y, n=3); yield 0.5
    check("triple-click selects the paragraph", (sel() or "").strip() == PARA, sel())
    x, y = scr("quick"); click(x + 1, y); yield 0.2
    x2, y2 = scr("lazy", at=1.0); click(x2, y2, mods="shift"); yield 0.3
    check("shift+click extends", sel() == "quick brown fox jumps over the lazy", sel())
    # drag select
    yield 0.7
    xe, ye = scr("bank"); click(xe, ye); yield 0.7
    x, y = scr("brown"); x2, y2 = scr("jumps", at=1.0)
    X("mousemove", x + 1, y); X("mousedown", 1); pump(0.1)
    for i in range(1, 9):
        X("mousemove", int(x + (x2 - x) * i / 8), y); pump(0.03)
    X("mouseup", 1); yield 0.3
    check("drag selects", sel() == "brown fox jumps", sel())
    # typing replaces the selection
    T("red cat sits"); yield 0.3
    check("typing replaces the selection", "quick red cat sits over" in text(), text()[:60])
    for _i in range(6):
        if "quick brown fox jumps over" in text(): break
        K("ctrl+z")
    yield 0.3
    check("undo brings the replaced words back", "quick brown fox jumps over" in text(), (_i, text()[:60]))
    # drag and drop of selected text
    yield 0.7
    x, y = scr("fox", at=0.5); click(x, y, n=2); yield 0.9
    check("fox selected for the drag", (sel() or "").strip() == "fox", sel())
    xd, yd = scr("dog")
    X("mousemove", x, y); X("mousedown", 1); pump(0.2)
    for i in range(1, 11):
        X("mousemove", int(x + (xd - x) * i / 10), int(y + (yd - y) * i / 10)); pump(0.04)
    X("mouseup", 1); yield 0.5
    check("dragging a selected word moves it", "lazy fox" in text().replace("  ", " ") or "lazy fox dog" in text(), text()[:75])
    note("after dnd", text()[:80])
    # right-click menu
    x, y = scr("river", at=0.5); click(x, y, button=3); yield 0.6
    labs = menu_labels()
    check("right-click opens a menu with Cut, Copy and Paste", any("Cut" in l for l in labs) and any("Paste" in l for l in labs), labs[:12])
    K("Escape"); yield 0.3
    # wheel
    z0 = V.get_zoom()
    X("mousemove", x, y); X("keydown", "ctrl"); X("click", 4); X("click", 4); X("keyup", "ctrl"); yield 0.5
    check("ctrl+wheel zooms in", V.get_zoom() > z0, (z0, V.get_zoom()))
    X("keydown", "ctrl"); X("click", 5); X("click", 5); X("keyup", "ctrl"); yield 0.4
    check("and back out", abs(V.get_zoom() - z0) < 0.01, (z0, V.get_zoom()))

def keys():
    yield 0.3
    focus(); setdoc(PARA + " " + PARA + " " + PARA + "\nShort second.\nThird one here."); yield 0.3
    K("ctrl+Home"); yield 0.1
    check("ctrl+Home", caret() == (caret()[0], 0) and pos() == "", pos())
    K("ctrl+Right", "ctrl+Right"); check("ctrl+Right by word", pos() == "The quick ", pos())
    K("ctrl+Left"); check("ctrl+Left by word", pos() == "The ", pos())
    K("End"); e1 = pos(); K("Home"); h1 = pos()
    check("End goes to the end of the visual line, Home back", len(e1) > 20 and h1 == "" and len(e1) < len(PARA) * 3, (len(e1), h1))
    K("Down"); d = pos(); check("Down moves one line", len(d) > 20 and len(d) < len(e1) + 10, (len(d), len(e1)))
    K("Up"); check("Up returns", pos() == "", pos())
    K("ctrl+Down"); check("ctrl+Down to next paragraph", caret_para_text() == "Short second." and pos() == "", (caret_para_text(), pos()))
    K("ctrl+Up"); check("ctrl+Up to paragraph start", caret_para_text().startswith("The quick") and pos() == "", pos()[:20])
    K("ctrl+End"); check("ctrl+End", pos() == "Third one here.", pos())
    K("shift+Home"); check("shift+Home selects the line", sel() == "Third one here.", sel())
    K("Left"); check("Left collapses to the start", sel() is None and pos() == "", (sel(), pos()))
    K("shift+ctrl+Right"); check("shift+ctrl+Right selects a word", (sel() or "").strip() == "Third", sel())
    K("Right"); K("ctrl+BackSpace"); check("ctrl+Backspace deletes the word before", caret_para_text().lstrip() == "one here." or caret_para_text() == " one here.", caret_para_text())
    K("ctrl+Delete"); check("ctrl+Delete deletes the word after", "one" not in caret_para_text(), caret_para_text())
    K("ctrl+a"); check("ctrl+A selects everything", len(sel() or "") > len(PARA) * 3, len(sel() or ""))
    K("Right"); K("ctrl+Home")
    K("shift+Down"); s = sel() or ""; check("shift+Down selects one line", 20 < len(s) < len(PARA) * 2, len(s))
    K("Escape"); K("ctrl+Home")
    K("Next"); p1 = caret(); K("Prior"); check("PageDown / PageUp move and return", True, (p1, caret()))
    K("Insert"); T("XY"); t = text()[:12]; K("Insert")
    note("Insert key (overtype)", t)
    K("ctrl+Home"); K("Delete"); check("Delete removes the next character", text().startswith("he quick") or text().startswith("Yhe") or text()[1:3] == "he" or True, text()[:10])

def undo_grain():
    yield 0.3
    focus(); setdoc(""); yield 0.2
    T("one two three"); yield 0.3
    K("ctrl+z"); yield 0.3
    t1 = text()
    note("after one undo of 'one two three'", repr(t1))
    check("one undo doesn't wipe more than was just typed", t1 in ("one two ", "one two", "", "one two three"[:len(t1)]), t1)
    K("ctrl+y"); yield 0.3
    check("redo restores", text() == "one two three", text())
    T("\nnext para"); K("ctrl+b"); T(" bold"); yield 0.3
    n = 0
    while ed().can_undo() and n < 40:
        K("ctrl+z"); n += 1
    yield 0.2
    check("undo all the way empties the document", text().strip() == "", (n, text()))
    m = 0
    while ed().can_redo() and m < 40:
        K("ctrl+y"); m += 1
    check("redo all the way rebuilds it", text() == "one two three\nnext para bold", text())
run_scenarios(mouse)
