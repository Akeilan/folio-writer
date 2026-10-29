import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
import zipfile
def a():
    yield 1.0
    focus(); yield 0.2
    ed = E.ed
    win.dialogs.message = lambda *a, **k: None
    ed.type_text("Before\n")
    ed.insert_table(3, 3)
    E.view.after_edit(); yield 0.3
    words = ["a", "longer words here", "x", "1", "22", "333", "p", "q", "r"]
    for i, w in enumerate(words):
        ed.type_text(w)
        if i < 8:
            ed.cell_step(False)
    E.view.after_edit(); yield 0.3
    ed.move_caret("doc_start", False); ed.move_caret("down", False)
    E.view.after_move()
    win.actions.cmd(".uno:EntireRow"); yield 0.2
    check("select row", ed.selected_text().replace("\n", "|").startswith("a|longer"), repr(ed.selected_text()))
    win.actions.cmd(".uno:SelectTable"); yield 0.2
    check("select table", "333" in ed.selected_text() and "r" in ed.selected_text())
    ed.move_caret("doc_start", False); ed.move_caret("down", False)
    win.actions.cmd(".uno:EntireColumn"); yield 0.2
    t = ed.selected_text()
    check("select column", "1" in t and "p" in t and "longer" not in t, repr(t))
    rs = ed.selection_rects()
    check("column rects", len(rs) == 3 and len(set(round(r[1]) for r in rs)) == 1, rs)
    # autofit contents: the long column gets wider
    ed.move_caret("doc_start", False); ed.move_caret("down", False); E.view.after_move()
    w0 = list(ed.grid_widths())
    win.actions.cmd(".uno:SelectTable"); win.actions.cmd(".uno:SetOptimalColumnWidth"); yield 0.3
    w1 = list(ed.grid_widths())
    check("autofit contents", w1[1] > w1[0] and w1[1] > w1[2] and sum(w1) < sum(w0), (w0, w1))
    # split a cell into 2 columns
    ed.move_caret("doc_start", False); ed.move_caret("down", False); E.view.after_move()
    ok = ed.split_cells(2, 1); E.view.after_edit(); yield 0.3
    check("split cells", ok and len(ed.grid_widths()) == 4, ed.grid_widths())
    # split into 2 rows
    ok = ed.split_cells(1, 2); E.view.after_edit(); yield 0.3
    win.save_to("/tmp/n19a.docx"); yield 0.5
    d = zipfile.ZipFile("/tmp/n19a.docx").read("word/document.xml").decode()
    check("split rows", d.count("<w:tr") == 4 and 'w:val="restart"' in d, d.count("<w:tr"))
    # distribute rows
    ok = ed.distribute_rows(); E.view.after_edit(); yield 0.2
    check("distribute rows", ok)
    # text direction on a cell
    ed.move_caret("doc_end", False); ed.move_caret("up", False); E.view.after_move()
    win.actions.model_call_sync if False else None
    win.model_call_sync("tablelayout.text_direction"); yield 0.4
    win.save_to("/tmp/n19b.docx"); yield 0.5
    d = zipfile.ZipFile("/tmp/n19b.docx").read("word/document.xml").decode()
    check("text direction", 'w:textDirection w:val="tbRl"' in d)
    shot("n19")
    # gridlines toggle
    win.actions.cmd(".uno:TableBoundaries"); yield 0.2
    check("gridlines off", not E.view.gridlines and not E.is_on(".uno:TableBoundaries"))
    win.actions.cmd(".uno:TableBoundaries"); yield 0.2
    # split table at the 2nd row
    ed.move_caret("doc_start", False); ed.move_caret("down", False)
    for _ in range(12):
        if ed.cell_name().endswith("2"):
            break
        ed.cell_step(False)
    E.view.after_move()
    ok = ed.split_table(); E.view.after_edit(); yield 0.3
    win.save_to("/tmp/n19c.docx"); yield 0.5
    d = zipfile.ZipFile("/tmp/n19c.docx").read("word/document.xml").decode()
    check("split table", ok and d.count("<w:tbl>") == 2, d.count("<w:tbl>"))
    p = ed.table_props()
    check("table props none outside", p is None)
run_scenarios(a)
