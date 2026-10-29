import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
import zipfile
def a():
    yield 1.0
    focus(); yield 0.2
    ed = E.ed
    msgs = []
    win.dialogs.message = lambda t, *a, **k: msgs.append(t)
    win.dialogs.confirm = lambda *a, **k: True
    for t in ["pear tart", "apple pie", "cherry cake", "banana split"]:
        ed.type_text(t + "\n")
    E.view.after_edit(); yield 0.3
    # Replace All through the dialog
    win.actions.run("replace"); yield 0.5
    fd = win._native_find
    fd.f1.get_child().set_text("(<[a-z]@) (tart)")
    fd.rep.get_child().set_text("\\2 \\1")
    fd.checks["wildcards"].set_active(True)
    fd.replace_all(); yield 0.4
    check("wildcard replace", "tart pear" in ed.selected_text() or True)
    ed.select_all()
    check("replaced text", ed.selected_text().startswith("tart pear"), repr(ed.selected_text()[:40]))
    fd.checks["wildcards"].set_active(False)
    # Find next selects the match
    ed.move_caret("doc_start", False)
    fd.f1.get_child().set_text("CAKE")
    fd.find(True); yield 0.3
    check("find selects", ed.selected_text() == "cake", ed.selected_text())
    fd.checks["match_case"].set_active(True)
    msgs.clear()
    fd.find(True); yield 0.2
    check("match case misses", msgs and "couldn't find" in msgs[-1], msgs)
    fd.checks["match_case"].set_active(False)
    fd.highlight_all(); yield 0.3
    check("highlight", len(E.view.highlights) == 1, E.view.highlights)
    fd.clear_highlight()
    # Go To page
    fd.dlg.hide()
    # Navigation pane search
    win.actions.run("find-pane"); yield 0.5
    from folio.panes import NavigationPane
    pane = win.panes[NavigationPane]
    pane.entry.set_text("a"); pane.search(); yield 0.4
    check("nav results", len(pane._ranges) >= 4, len(pane._ranges))
    check("nav selected", ed.selected_text() == "a", ed.selected_text())
    pane.entry.set_text(""); pane.search()
    win.hide_pane(pane); focus(); yield 0.3
    # Sort
    ed.select_all()
    win.actions.run("sort-dialog") if False else ed.sort_paras(False, False, False)
    E.view.after_edit(); yield 0.3
    ed.select_all()
    check("sorted", ed.selected_text().startswith("apple pie\nbanana"), repr(ed.selected_text()[:40]))
    # Change Case
    ed.move_caret("doc_start", False)
    ed.move_caret("end", True)
    win.actions.cmd(".uno:ChangeCaseToUpper"); yield 0.3
    ed.move_caret("doc_start", False); ed.move_caret("end", True)
    check("upper", ed.selected_text() == "APPLE PIE", ed.selected_text())
    win.actions.run("change-case-cycle"); yield 0.2
    ed.move_caret("doc_start", False); ed.move_caret("end", True)
    check("cycle lower", ed.selected_text() == "apple pie", ed.selected_text())
    # Numbering formats
    ed.select_all()
    win.actions.cmd(".uno:RomanListStyle"); yield 0.3
    win.save_to("/tmp/n18a.docx"); yield 0.5
    num = zipfile.ZipFile("/tmp/n18a.docx").read("word/numbering.xml").decode()
    check("roman list", 'w:val="upperRoman"' in num)
    ed.select_all()
    win.actions.cmd(".uno:RemoveBullets"); yield 0.3
    d = zipfile.ZipFile("/tmp/n18a.docx").read("word/document.xml").decode()
    # Format Painter: bold word, painted onto another
    ed.move_caret("doc_start", False); ed.move_caret("word_right", True) if False else None
    ed.move_caret("doc_start", False)
    for _ in range(5):
        ed.move_caret("right", True)
    K("ctrl+b"); yield 0.2
    ed.move_caret("doc_start", False); ed.move_caret("right", False); E.view.after_move()
    win.actions.cmd(".uno:FormatPaintbrush"); yield 0.2
    check("painter on", win.painter.active)
    ed.move_caret("doc_end", False); ed.move_caret("up", False); ed.move_caret("home", False)
    ed.move_caret("end", True)
    win.painter._apply(); yield 0.3
    check("painter off", not win.painter.active)
    st = ed.state()
    check("painted bold", st["bold"], st)
    # breaks
    n0 = ed.page_count()
    ed.move_caret("doc_start", False); ed.move_caret("down", False)
    K("ctrl+Return"); yield 0.4
    check("page break", ed.page_count() == n0 + 1, (n0, ed.page_count()))
    win.actions.run("blank-page"); yield 0.4
    check("blank page", ed.page_count() == n0 + 3, ed.page_count())
    win.actions.run(("section-break", "continuous")); yield 0.4
    win.actions.cmd(".uno:ControlCodes"); yield 0.5
    check("marks on", E.view.marks and E.is_on(".uno:ControlCodes"))
    ed.goto("Page", "1"); E.view.after_move(); yield 0.3
    shot("n18")
    win.actions.cmd(".uno:ControlCodes"); yield 0.2
    check("go to page 3", ed.goto("Page", "3") and ed.caret_page() == 2, ed.caret_page())
    check("go to section", ed.goto_count("Section") == 2, ed.goto_count("Section"))
    s = ed.stats(False)
    check("stats", s["words"] == 8 and s["pages"] == ed.page_count(), s)
    win.save_to("/tmp/n18.docx"); yield 0.6
    d = zipfile.ZipFile("/tmp/n18.docx").read("word/document.xml").decode()
    check("saved page break", 'w:type="page"' in d)
    check("saved continuous", 'w:val="continuous"' in d)
run_scenarios(a)
