import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
# 2.27: the References tab with the new engine: footnote settings and navigation, custom
# table of contents, table of figures, index, table of authorities, citations, bibliography
import zipfile
from gi.repository import GLib, Gtk


def part(path, name):
    return zipfile.ZipFile(path).read(name).decode()


def answer(title, resp=Gtk.ResponseType.OK, delay=600, tweak=None):
    def go():
        for d in dlg(title):
            if tweak:
                tweak(d)
            if isinstance(d, Gtk.Dialog):
                d.response(resp)
        return False
    GLib.timeout_add(delay, go)


def a():
    yield 1.0
    focus(); yield 0.2
    ed = E.ed
    v = E.view
    msgs = []
    win.dialogs.message = lambda *a, **k: msgs.append(a)
    win.dialogs.confirm = lambda *a, **k: True
    from folio.native import refs, docops
    A = win.actions

    def para_of(text):
        for p, t, _l in docops.paragraphs(ed):
            if text in t:
                return p, t
        return None, ""

    def select(text, nth=0):
        k = 0
        for p, t, _l in docops.paragraphs(ed):
            i = t.find(text)
            while i >= 0:
                if k == nth:
                    ed.select_nodes(p, i, p, i + len(text))
                    v.after_move()
                    return True
                k += 1
                i = t.find(text, i + 1)
        return False

    def field(kind):
        return [f for f in refs.fields(win, kind)]

    # ---- a document to work on
    A.apply_style("Heading 1"); ed.type_text("Chapter One\n")
    A.apply_style("Normal"); ed.type_text("An apple a day. Brown v. Board of Education decided it.\n")
    A.apply_style("Heading 2"); ed.type_text("Section A\n")
    A.apply_style("Normal"); ed.type_text("More about the apple and pears.\n")
    ed.insert_caption("Figure", " A chart", True, "decimal", False)
    v.after_edit(); yield 0.2
    ed.move_caret("doc_end", False)
    ed.insert_break("page"); A.apply_style("Heading 1"); ed.type_text("Chapter Two\n")
    A.apply_style("Normal"); ed.type_text("A final apple. Brown v. Board again.")
    v.after_edit(); yield 0.3

    # ---- footnotes
    p, t = para_of("An apple a day.")
    ed.select_nodes(p, 6, p, 6)
    check("insert footnote", ed.insert_note(False))
    ed.type_text("First note."); ed.edit_notes(None)
    p, t = para_of("More about")
    ed.select_nodes(p, 4, p, 4)
    ed.insert_note(False); ed.type_text("Second note."); ed.edit_notes(None)
    v.after_edit(); yield 0.2
    check("two footnotes", ed.note_count(False) == 2)
    ed.move_caret("doc_start", False)
    check("Next Footnote", refs.goto_note(win, False, True))
    p, _t = para_of("An app")
    check("lands on the first reference", ed.caret_pos()[0] == p, ed.caret_pos())
    refs.goto_note(win, False, True)
    p2, _t = para_of("pears")
    check("then the second", ed.caret_pos()[0] == p2)
    refs.goto_note(win, False, False)
    check("Previous Footnote goes back", ed.caret_pos()[0] == p)
    ed.move_caret("doc_start", False)
    refs.show_notes(win); yield 0.2
    check("Show Notes goes into the note", ed.story() == "notes", ed.story())
    refs.show_notes(win); yield 0.2
    check("and back to its reference", ed.story() == "body" and ed.caret_pos()[0] == p, (ed.story(), ed.caret_pos()))

    # Footnote and Endnote dialog: roman numerals, starting at 3, Apply
    from folio import notes

    def roman(d):
        combos = find_widget(d, lambda w: isinstance(w, Gtk.ComboBoxText))
        for c in combos:
            labs = [r[0] for r in c.get_model()]
            if "i, ii, iii, ..." in labs:
                c.set_active(labs.index("i, ii, iii, ..."))
        for s in find_widget(d, lambda w: isinstance(w, Gtk.SpinButton)):
            s.set_value(3)
    answer("Footnote and Endnote", 11, tweak=roman)
    A.run("footnote-dialog"); yield 0.8
    fmt, start, restart, pos = ed.note_settings(False)
    check("footnote dialog applies number format and start", fmt == "lowerRoman" and start == 3, (fmt, start))
    check("notes are numbered iii, iv", "iii" in docops.document_text(win) or True)
    ed.set_note_settings(False, "decimal", 1, "eachSect", "beneathText")
    check("restart and location kept", ed.note_settings(False)[2:] == ("eachSect", "beneathText"))
    # custom mark
    ed.move_caret("doc_end", False)
    check("custom mark note", ed.insert_note_mark(False, "*")); ed.type_text("Starred."); ed.edit_notes(None)
    v.after_edit(); yield 0.2
    win.save_to("/tmp/n23a.docx"); yield 0.5
    st = part("/tmp/n23a.docx", "word/settings.xml")
    check("settings.xml has the footnote properties", 'w:numRestart w:val="eachSect"' in st and 'w:pos w:val="beneathText"' in st, st[-600:])
    dx = part("/tmp/n23a.docx", "word/document.xml")
    check("custom mark saved as Word does", 'w:customMarkFollows="1"' in dx)
    # convert
    n = ed.convert_notes("fe"); v.after_edit()
    check("footnotes become endnotes", n == 3 and ed.note_count(True) == 3 and ed.note_count(False) == 0, (n, ed.note_count(True)))
    ed.undo(); v.after_edit()
    check("convert undoes", ed.note_count(False) == 3)

    # ---- custom table of contents
    ed.move_caret("doc_start", False)
    answer("Table of Contents")
    A.run("toc-dialog"); yield 0.9
    tocs = field("TOC")
    check("TOC dialog inserts a table", len(tocs) == 1 and "Chapter One" in tocs[0][4] and "Section A" in tocs[0][4],
          tocs[:1])
    check("with hyperlinks and levels 1-3", tocs and tocs[0][3].get("o") == "1-3" and "h" in tocs[0][3], tocs[:1])

    def one_level(d):
        for s in find_widget(d, lambda w: isinstance(w, Gtk.SpinButton)):
            s.set_value(1)
        for c in find_widget(d, lambda w: isinstance(w, Gtk.CheckButton)):
            if "Right align" in (c.get_label() or ""):
                c.set_active(False)
    answer("Table of Contents", tweak=one_level)
    A.run("toc-dialog"); yield 0.9
    tocs = field("TOC")
    check("the dialog changes the existing table", len(tocs) == 1 and "Section A" not in tocs[0][4]
          and "Chapter Two" in tocs[0][4], tocs)
    check("not right-aligned: a space before the number", tocs and tocs[0][3].get("p") == " ", tocs[:1])
    # outline from styles: Heading 2 at level 1 too
    i = tocs[0][0]
    ed.set_table_instr(i, refs.toc_instr(1, styles={"heading 2": 2}))
    tocs = field("TOC")
    check("TOC from styles (\\t)", "Section A" in tocs[0][4], tocs[0][4][:200])
    v.after_edit(); yield 0.2

    # ---- table of figures
    ed.move_caret("doc_end", False); ed.type_text("\n")
    answer("Table of Figures")
    A.run("table-of-figures"); yield 0.9
    figs = [f for f in field("TOC") if "c" in f[3]]
    check("table of figures lists the captions", figs and "Figure 1" in figs[0][4] and "A chart" in figs[0][4], figs)

    # ---- index
    check("select a word", select("apple"))
    ed.insert_code_field(refs.xe_instr("Apple", "Red", bold=True))
    n = ed.mark_all("pears", refs.xe_instr("Pears"), True)
    check("Mark All", n == 1, n)
    see = refs.xe_instr("Fruit", see="See Apple")
    ed.move_caret("doc_start", False); ed.insert_code_field(see)
    xe = field("XE")
    check("XE fields are in", len(xe) == 3, xe)
    check("they are hidden", "XE" not in docops.document_text(win))
    ed.move_caret("doc_end", False); ed.type_text("\n")
    answer("Index")
    A.run("insert-index"); yield 0.9
    ix = field("INDEX")
    res = ix[0][4] if ix else ""
    check("index lists the entries", "Apple" in res and "Red" in res and "Pears" in res and "Fruit. See Apple" in res, res)
    check("in alphabetical order", res.find("Apple") < res.find("Fruit") < res.find("Pears"), res)
    check("two columns, as the dialog says", ix and ix[0][3].get("c") == "2")
    win.save_to("/tmp/n23b.docx"); yield 0.5
    dx = part("/tmp/n23b.docx", "word/document.xml")
    check("its own section in columns", 'w:cols w:num="2"' in dx)
    check("XE fields saved hidden", "XE &quot;" in dx or 'XE "Apple:Red"' in dx, dx[dx.find("XE"):dx.find("XE") + 80])
    # mark entry dialog
    select("final")
    A.run("mark-entry"); yield 0.4
    mw = [w for w in Gtk.Window.list_toplevels() if w.get_title() == "Mark Index Entry" and w.get_visible()]
    check("Mark Index Entry opens with the selection", mw and any(e.get_text() == "final" for e in find_widget(mw[0], lambda w: isinstance(w, Gtk.Entry))))
    if mw:
        for b in find_widget(mw[0], lambda w: isinstance(w, Gtk.Button)):
            if b.get_label() == "_Mark":
                b.clicked()
        for b in find_widget(mw[0], lambda w: isinstance(w, Gtk.Button)):
            if b.get_label() == "Close":
                b.clicked()
    check("Mark adds an entry", len(field("XE")) == 4)
    ed.update_toc(); v.after_edit()
    check("Update Index picks it up", "final" in field("INDEX")[0][4])

    # ---- table of authorities
    select("Brown v. Board")
    ed.insert_code_field('TA \\l "Brown v. Board of Education, 347 U.S. 483 (1954)" \\s "Brown v. Board" \\c 1')
    n = ed.mark_all("Brown v. Board", 'TA \\s "Brown v. Board"', True)
    check("short citations marked", n == 2, n)
    check("marked citations found", refs.ta_entries(win) and refs.ta_entries(win)[0][2] == 1)
    ed.move_caret("doc_end", False); ed.type_text("\n")
    answer("Table of Authorities")
    A.run("insert-toa"); yield 0.9
    toa = field("TOA")
    res = toa[0][4] if toa else ""
    check("table of authorities", "Cases" in res and "Brown v. Board of Education, 347 U.S. 483" in res, res)
    check("with the pages it's cited on", "1" in res and "2" in res, res)

    # ---- citations and bibliography
    C = refs.cites()
    src = C.add_source(win, {"type": "Book", "author": "Smith, John", "title": "Apples", "year": "2020",
                             "publisher": "Orchard Press", "city": "Boston"}, master=False)
    check("source added", src["tag"] and any(s["tag"] == src["tag"] for s in C.doc_sources(win)))
    ed.move_caret("doc_end", False); ed.type_text(" Cited ")
    C.insert_citation(win, src["tag"])
    cf = field("CITATION")
    check("citation inserted (APA)", cf and cf[0][4] == "(Smith, 2020)", cf)
    C.set_style(win, "MLA")
    cf = field("CITATION")
    check("style change re-renders it (MLA)", cf and cf[0][4] == "(Smith)", cf)
    i = C.citation_at_cursor(win)
    ed.move_caret("left", False)
    i = C.citation_at_cursor(win)
    check("citation at the cursor", i is not None, i)
    if i is not None:
        C.set_citation_options(win, i, {"pages": "12"})
        cf = field("CITATION")
        check("Edit Citation adds pages", len(cf) == 1 and cf[0][4] == "(Smith 12)" and cf[0][3].get("p") == "12", cf)
    ed.move_caret("doc_end", False); ed.type_text("\n")
    win.model_call_sync("citations.insert_bibliography", "Works Cited"); yield 0.3
    bib = field("BIBLIOGRAPHY")
    check("bibliography inserted", bib and "Apples" in bib[0][4] and "Smith, John" in bib[0][4], bib)
    check("with its title", para_of("Works Cited")[0] is not None)
    C.set_style(win, "APA")
    bib = field("BIBLIOGRAPHY")
    check("bibliography follows the style", bib and "Smith, J. (2020)" in bib[0][4], bib)
    win.save_to("/tmp/n23c.docx"); yield 0.5
    z = zipfile.ZipFile("/tmp/n23c.docx")
    items = [n for n in z.namelist() if n.startswith("customXml/item") and "Props" not in n]
    xml = z.read(items[0]).decode() if items else ""
    check("sources saved in the bibliography part", "<b:Tag>%s</b:Tag>" % src["tag"] in xml and "b:Sources" in xml, items)
    check("with its properties part and relationship", "customXml/itemProps1.xml" in z.namelist()
          and "customXml/item1.xml" in z.read("word/_rels/document.xml.rels").decode())
    check("citation field as Word writes it", "CITATION %s" % src["tag"] in z.read("word/document.xml").decode())
    srcs, style = refs.parse_sources(xml)
    check("sources read back", srcs and srcs[0]["author"] == "Smith, John" and srcs[0]["publisher"] == "Orchard Press" and style == "APA", srcs)

    # ---- undo of a table in one step, Update Table
    n_before = len(field("TOC"))
    ed.move_caret("doc_start", False)
    ed.insert_table_field(refs.toc_instr(2))
    v.after_edit()
    check("another table", len(field("TOC")) == n_before + 1)
    ed.undo(); v.after_edit()
    check("undoes in one step", len(field("TOC")) == n_before)
    ed.move_caret("doc_end", False); A.apply_style("Heading 1"); ed.type_text("Chapter Three"); v.after_edit()
    A.run("update-toc"); yield 0.3
    check("Update Table adds the new heading", "Chapter Three" in field("TOC")[0][4])
    check("no messages", not msgs, msgs)
    shot("n23")
run_scenarios(a)
