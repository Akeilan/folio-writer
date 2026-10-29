import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
def a():
    yield 1.0
    focus(); yield 0.2
    win.dialogs._new_table(4, 3); yield 0.4
    for t in ("Item", "Qty", "Price", "Pens", "4", "2.50", "Ink", "1", "9.00"):
        T(t); K("Tab")
    yield 0.4
    win.run(("table-style2", ("grid4", 0x4472C4))); yield 0.5
    info = E.ed.table_info()
    check("style applied", info["style"] == "GridTable4-Accent1", info)
    win.run(("table-option", "banded_rows")); yield 0.3
    check("banding off", not E.ed.table_info()["banded_rows"], E.ed.table_info())
    win.run(("table-option", "banded_rows")); yield 0.3
    win.run(".uno:TableCellBackgroundColor") ; yield 0.2
    from folio import bordermenu
    bordermenu.apply_win(win, "outside"); yield 0.3
    win.model_call_sync("tablelayout.align_cells", "center", "center"); yield 0.3
    win.model_call_sync("tablelayout.set_row_height", 1000); yield 0.3
    shot("n6")
    ok = win.save_to("/tmp/n6.docx"); yield 1.0
    check("saved", ok)
    import zipfile
    st = zipfile.ZipFile("/tmp/n6.docx").read("word/styles.xml").decode()
    check("style definition saved", 'w:styleId="GridTable4-Accent1"' in st and "tblStylePr" in st)
run_scenarios(a)
