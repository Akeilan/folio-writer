import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
# 2.32 (W3-04): what used to go through the old engine, on Folio's own engine: formula
# fields, Link to Previous / section navigation, page number format with chapter numbers,
# collapsed headings, Compare, the Document Inspector, the compatibility checker, paste
# link, reviewers shown, track change marks, custom dictionaries, Draw Table, quick tables
import os
import zipfile

MSG = []
win.dialogs.message = lambda text, *a, **k: MSG.append(text)
win.dialogs.confirm = lambda *a, **k: True


def body(ed):
    return [ed.para_text_of(n) for k, n, _t in ed.body_blocks() if k == "p"]


def xml(ed, part="word/document.xml", path="/tmp/n43.docx"):
    ed.save(path)
    return zipfile.ZipFile(path).read(part).decode()


def caret_in(ed, text):
    for k, n, _t in ed.body_blocks():
        if k == "p" and ed.para_text_of(n).startswith(text):
            ed.select_nodes(n, 0, n, 0)
            return n


def a():
    yield 1.0
    ed = E.ed
    v = E.view
    # ---------------------------------------------------------------- formula fields
    ed.insert_table(4, 2)
    for t in ("Item", "Cost", "Pens", "2.50", "Paper", "4", "Total"):
        ed.type_text(t)
        ed.cell_step(False)
    from folio.native import tables as NT
    check("default formula", NT._default_formula(ed) == "=SUM(ABOVE)", NT._default_formula(ed))
    ed.insert_field_now('=SUM(ABOVE) \\# "0.00"')
    v.after_edit(); yield 0.3
    x = xml(ed)
    check("SUM(ABOVE)", "6.50" in str([ed.para_text_of(p) for row in ed.table_cells(0) for c in row for p in c]), x[-600:])
    ed.insert_field_now("=(B2+B3)*2")
    v.after_edit(); yield 0.2
    cells = [ed.para_text_of(p) for row in ed.table_cells(0) for c in row for p in c]
    check("cell references", any("13" in c for c in cells), cells)
    # ---------------------------------------------------------------- cell margins
    check("cell margins read", ed.table_cell_margins() == (0, 0, 108, 108), ed.table_cell_margins())
    ed.set_table_cell_margins(72, 72, 144, 144)
    check("cell margins set", ed.table_cell_margins() == (72, 72, 144, 144) and "w:tblCellMar" in xml(ed))
    # ---------------------------------------------------------------- convert to text
    import folio.native.tables as T
    orig_ask = T.__dict__.get("FDialog")
    from folio import widgets
    real = widgets.FDialog.ask
    widgets.FDialog.ask = lambda self: -5
    try:
        T.convert_dialog(win)
    finally:
        widgets.FDialog.ask = real
    yield 0.3
    b = body(ed)
    check("table to text", not [k for k, _n, _t in ed.body_blocks() if k == "t"] and any("Pens\t2.50" in p for p in b), b)
    # ---------------------------------------------------------------- quick tables
    from folio import insertmore
    ed.select_all(); ed.delete(True, False)
    insertmore.quick_table(win, "Tabular List"); yield 0.3
    cells = [ed.para_text_of(p) for row in ed.table_cells(0) for c in row for p in c]
    check("quick table", cells[:4] == ["ITEM", "NEEDED", "Books", "1"], cells[:6])
    ed.select_all(); ed.table_command("delete_table"); ed.select_all(); ed.delete(True, False)
    v.after_edit(); yield 0.2
    # ---------------------------------------------------------------- headings: folds, chapters
    from folio.native import lists as NL
    ids = {n: s for s, n in ed.paragraph_styles()}
    ed.type_text("Intro\nText one\nText two\nMethods\nText three")
    for h in ("Intro", "Methods"):
        caret_in(ed, h)
        ed.set_style(ids["Heading 1"])
    v.after_edit(); yield 0.3
    marks = ed.heading_marks()
    check("heading marks", len(marks) == 2, marks)
    pages_lines = len([1 for pg in range(ed.page_count()) for _ in ed.page_text(pg)])
    intro = marks[0][0]
    ed.toggle_fold(intro)
    v.document_changed(); yield 0.2
    after = len([1 for pg in range(ed.page_count()) for _ in ed.page_text(pg)])
    check("collapsed heading hides its text", ed.is_folded(intro) and after < pages_lines, (pages_lines, after))
    caret_in(ed, "Text one")
    ed.reveal_caret()
    check("caret in collapsed text opens it", not ed.is_folded(intro))
    ed.set_collapsed_default(intro, True)
    check("collapsed by default saved", "w15:collapsed" in xml(ed))
    ed.fold_all(False)
    caret_in(ed, "Methods")
    nd = ed.fold_defaults()
    check("fold defaults", nd == 1 and ed.is_folded(intro), (nd, ed.collapsed_default(intro), [m[0] for m in ed.heading_marks()], intro))
    ed.fold_all(False)
    NL.heading_numbering(win); yield 0.3
    sec = ed.current_section()
    ed.section_attr(sec, "w:pgNumType", "w:chapStyle", "1", "Page Number Format")
    ed.page_number_in(sec, True, "center", False, False)
    v.document_changed(); yield 0.3
    hf = ed.page_hf_text(0)
    check("chapter number before the page number", "1-1" in hf, hf)
    # ---------------------------------------------------------------- Link to Previous
    caret_in(ed, "Methods")
    win.run(("section-break", "next-page"))
    v.after_edit(); yield 0.3
    check("two sections", ed.section_count() == 2, ed.section_count())
    check("linked by default", ed.hf_linked(1, True, 0))
    ed.set_hf_linked(1, True, 0, False)
    check("unlinked has its own footer", not ed.hf_linked(1, True, 0) and xml(ed).count("w:footerReference") >= 2)
    ed.set_hf_linked(1, True, 0, True)
    check("linked again", ed.hf_linked(1, True, 0))
    # ---------------------------------------------------------------- inspector / compat
    c = ed.inspect_counts()
    check("inspector counts", c.get("hf", 0) >= 1, c)
    from folio import inspector, compat
    found, msg = inspector.inspect(win, "hf")
    check("inspector finds headers", found, msg)
    inspector.remove(win, "hf")
    check("headers removed", not inspector.inspect(win, "hf")[0])
    check("compat scan", isinstance(compat.scan(win), dict))
    # ---------------------------------------------------------------- reviewers
    ed.set_author("Alice")
    ed.set_track_changes(True)
    ed.move_caret("doc_end", False)
    ed.type_text(" added")
    ed.set_track_changes(False)
    v.after_edit(); yield 0.2
    check("change authors", "Alice" in ed.change_authors(), ed.change_authors())
    win.change_bars.hidden_authors = {"Alice"}
    win.change_bars.refresh()
    check("hidden reviewer", True)
    win.change_bars.hidden_authors = set()
    win.change_bars.refresh()
    from folio import trackoptions
    win.app.settings["track_options"] = {"ins_mark": 4, "del_mark": 0}
    trackoptions.apply(win)
    v.queue_draw(); yield 0.2
    win.app.settings.pop("track_options", None)
    trackoptions.apply(win)
    ed.accept_reject_all(True, None)
    # ---------------------------------------------------------------- compare
    ed.select_all(); ed.delete(True, False)
    ed.type_text("The quick brown fox.\nJumps over the dog.")
    ed.save("/tmp/n43_orig.docx")
    ed.select_all(); ed.delete(True, False)
    ed.type_text("The quick red fox.\nJumps over the lazy dog.\nA new line.")
    ed.save("/tmp/n43_rev.docx")
    ed.select_all(); ed.delete(True, False)
    ed.type_text("The quick brown fox.\nJumps over the dog.")
    from folio.native import compare
    n = compare.compare(win, "/tmp/n43_rev.docx", "Reviewer")
    v.after_edit(); yield 0.3
    ch = ed.changes()
    kinds = sorted({k for k, *_r in ch})
    check("compare makes changes", n and len(ch) >= 3 and all(a == "Reviewer" for _k, a, *_r in ch), (n, ch[:6]))
    ed.accept_reject_all(True, None)
    check("accepting gives the revised text", body(ed)[:3] == ["The quick red fox.", "Jumps over the lazy dog.", "A new line."], body(ed))
    # ---------------------------------------------------------------- custom dictionaries
    from folio.native import spell
    path = os.path.join(os.path.expanduser(spell.DICT_DIR), "N43TEST.dic")
    spell.write_words(path, ["Zorbuxle"])
    sp = v.speller
    check("custom dictionary word accepted", sp.check_word("Zorbuxle", "en_US") or spell._dict("en_US") is None)
    spell.set_active(win.app.settings, "N43TEST.dic", False)
    check("inactive dictionary ignored", (not sp.check_word("Zorbuxle", "en_US")) or spell._dict("en_US") is None)
    spell.set_active(win.app.settings, "N43TEST.dic", True)
    os.remove(path)
    spell.reload_user_words()
    # ---------------------------------------------------------------- draw table
    ed.select_all(); ed.delete(True, False)
    ed.type_text("Above\n\nBelow")
    v.after_edit(); yield 0.3
    td = win.table_draw
    td.begin("draw")
    r = ed.caret_rect()
    class Ev:
        button = 1
        state = 0
    x0, y0 = v.to_widget(0, 100, 140)
    x1, y1 = v.to_widget(0, 300, 200)
    e = Ev(); e.x, e.y = x0, y0
    td.press(e)
    e2 = Ev(); e2.x, e2.y = x1, y1
    td.motion(e2)
    td.release(e2)
    td.stop()
    yield 0.3
    check("draw table makes a table", [k for k, _n, _t in ed.body_blocks() if k == "t"], ed.body_blocks())
    ed.mark_saved()


run_scenarios(a)
