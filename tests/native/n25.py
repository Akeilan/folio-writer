exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
# 2.29 (views): Draft, Web Layout, Outline view, Read Mode, Immersive Reader, Read Aloud,
# Split, New Window
from gi.repository import GLib, Gtk


def a():
    yield 1.0
    focus(); yield 0.2
    ed = E.ed
    v = E.view
    msgs = []
    win.dialogs.message = lambda *a, **k: msgs.append(a)
    A = win.actions
    A.apply_style("Heading 1"); ed.type_text("Chapter One\n")
    A.apply_style("Normal"); ed.type_text("First chapter text. " * 30 + "\n")
    A.apply_style("Heading 2"); ed.type_text("Part A\n")
    A.apply_style("Normal"); ed.type_text("Text of part A.\n")
    ed.insert_break("page")
    A.apply_style("Heading 1"); ed.type_text("Chapter Two\n")
    A.apply_style("Normal"); ed.type_text("Second chapter text.")
    v.after_edit(); yield 0.3
    pages_print = ed.page_count()
    check("two pages in Print Layout", pages_print == 2, pages_print)

    # ---- draft
    A.run("draft-view"); yield 0.4
    check("Draft: no page break, one strip", ed.view_mode() == 1 and ed.page_count() == 1, ed.page_count())
    w, h = ed.page_size(0)
    check("Draft: no margins round the text", w < 500, (w, h))
    check("the view draws it edge to edge", v.continuous)
    shot("n25_draft")
    ed.type_text(" More."); v.after_edit()
    check("typing works in Draft", "More." in "".join(t for _p, t, _l in __import__("folio.native.docops", fromlist=["x"]).paragraphs(ed)))
    ed.undo(); v.after_edit()

    # ---- web layout
    A.run("web-layout"); yield 0.6
    w2, _h = ed.page_size(0)
    alloc = v.get_allocated_width() / v.ppp
    check("Web Layout: as wide as the window", ed.view_mode() == 2 and abs(w2 - alloc) < 6, (w2, alloc))
    shot("n25_web")
    A.run("print-layout"); yield 0.4
    check("back to Print Layout", ed.view_mode() == 0 and ed.page_count() == pages_print and not v.continuous)

    # ---- outline
    A.run("outline-view"); yield 0.5
    ov = win.outline()
    check("Outline view opens", ov is not None)
    rows = []

    def walk(it, depth=0):
        while it is not None:
            rows.append((depth, ov.store[it][2], ov.store[it][3].text[:12], ov.store[it][1]))
            walk(ov.store.iter_children(it), depth + 1)
            it = ov.store.iter_next(it)
    walk(ov.store.get_iter_first())
    check("headings and their text, nested", rows[0][:3] == (0, 1, "Chapter One") and any(r[2] == "Part A" and r[0] == 1 for r in rows), rows)
    check("outline symbols", rows[0][3] == "⊕" and any(r[3] == "○" for r in rows))
    ov.show_level(1); yield 0.2
    top = [ov.store[it][3].text for it in [ov.store.get_iter_first()]]
    check("Show Level 1: only the chapters", len(ov.store) == 2 and ov.store.iter_n_children(ov.store.get_iter_first()) == 0, len(ov.store))
    ov.show_level(9); yield 0.2
    # select Chapter Two and move it up
    it = ov.store.get_iter_first()
    it2 = ov.store.iter_next(it)
    ov.tv.get_selection().select_iter(it2)
    ov.move(-1); yield 0.3
    first = ov.store[ov.store.get_iter_first()][3].text
    check("Move Up moves the whole section", first == "Chapter Two", first)
    ed_paras = [r[1] for r in ed.outline_paras()]
    check("in the document too", ed_paras[0] == "Chapter Two" and ed_paras.index("Part A") > ed_paras.index("Chapter One"), ed_paras[:5])
    ov.tv.get_selection().select_iter(ov.store.get_iter_first())
    ov.change_level(1); yield 0.2
    check("Demote makes it Heading 2", [r for r in ed.outline_paras() if r[1] == "Chapter Two"][0][2] == 2)
    ed.undo(); ed.undo(); v.after_edit()
    win.act_close_outline(); yield 0.2
    check("Close Outline View", win.outline() is None)

    # ---- read mode
    ed.move_caret("doc_start", False)
    A.run("read-mode"); yield 0.6
    from folio.readmode import ReadMode
    rm = win.alt_view
    check("Read Mode", isinstance(rm, ReadMode) and len(rm.pages) == ed.page_count())
    s = rm._surface(0, 400)
    check("Read Mode draws the pages", s is not None and s.get_width() >= 399, s)
    shot("n25_read")
    rm.leave(); yield 0.3
    check("leaves Read Mode", win.alt_view is None)

    # ---- immersive reader
    A.run("immersive-reader"); yield 0.5
    ir = win.immersive()
    text = ir.buf.get_text(ir.buf.get_start_iter(), ir.buf.get_end_iter(), False) if ir else ""
    check("Immersive Reader shows the text", ir is not None and "Chapter One" in text and "Part A" in text)
    ir.syllables = True
    ir.load()
    text = ir.buf.get_text(ir.buf.get_start_iter(), ir.buf.get_end_iter(), False)
    check("Syllables", "·" in text, text[:80])
    src = ir.source()
    check("Read Aloud reads its text", len(src) >= 4 and src.words(0))
    win.act_close_immersive(); yield 0.2

    # ---- read aloud from the caret
    from folio.native.views import DocSource
    ed.move_caret("doc_start", False)
    ds = DocSource(win)
    check("Read Aloud starts at the caret", len(ds) >= 4 and ds.words(0)[0][2] in ("Chapter",), ds.words(0)[:2])
    ds.highlight(1, 0, 5)
    check("and highlights the word being read", ed.has_selection() and len(ed.selected_text()) == 5)

    # ---- split and new window
    A.run("split"); yield 0.4
    check("Split", win.split_view is not None)
    v2 = win.split_view[2]
    check("a second view of the same document", v2.ed is ed)
    ed.move_caret("doc_end", False); ed.type_text(" Split!"); v.after_edit(); yield 0.2
    check("both views update", v2.ed.version == ed.version)
    A.run("split"); yield 0.2
    check("Remove Split", win.split_view is None)
    A.run("new-window"); yield 0.5
    extra = getattr(win, "extra_windows", [])
    check("New Window", len(extra) == 1 and ":2" in extra[0].get_title(), [w.get_title() for w in extra])
    for w in list(extra):
        w.destroy()
    check("no messages", not msgs, msgs)
run_scenarios(a)
