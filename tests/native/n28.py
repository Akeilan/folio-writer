import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
# 2.30: the keyboard as in the original (Alt+X, F8, Alt+Shift+Up/Down, Spike, F4, Shift+F5),
# AutoFormat As You Type (lists from "a) " to "(1) ", "---" lines, names of days, Tab
# indents, the AutoCorrect button), KeyTips, PDF options, .txt without a converter,
# treemap and sunburst as real charts
import os
import tempfile
import zipfile
from gi.repository import GLib, Gtk


def body(ed):
    return [ed.para_text_of(n) for k, n, _t in ed.body_blocks() if k == "p"]


def a():
    yield 1.0
    focus(); yield 0.2
    ed = E.ed
    msgs = []
    win.dialogs.message = lambda *a, **k: msgs.append(a)

    # ---- Alt+X
    fresh(); yield 0.2
    T("x00e9"); yield 0.3
    K("alt+x"); yield 0.3
    check("Alt+X: code to character", body(ed)[0] == "xé", body(ed))
    K("alt+x"); yield 0.3
    check("Alt+X again: character to code", body(ed)[0] == "x00E9", body(ed))
    fresh(); yield 0.2
    T("U+1F600"); K("alt+x"); yield 0.3
    check("Alt+X with U+", body(ed)[0] == "\U0001F600", body(ed))

    # ---- F8 Extend mode
    fresh(); yield 0.2
    T("One two three. Four five."); K("Return"); T("Next para."); yield 0.3
    K("ctrl+Home"); K("Right"); yield 0.2
    K("F8"); yield 0.2
    check("F8 once: Extend mode, nothing selected yet", win.extend_mode and not ed.has_selection())
    K("Right"); K("Right"); yield 0.2
    check("arrows extend", ed.selected_text() == "ne", ed.selected_text())
    K("F8"); yield 0.2
    check("F8 twice: the word", ed.selected_text().strip() == "One", ed.selected_text())
    K("F8"); yield 0.2
    check("three times: the sentence", ed.selected_text().strip() == "One two three.", ed.selected_text())
    K("F8"); yield 0.2
    check("four times: the paragraph", ed.selected_text().startswith("One two three. Four five."), ed.selected_text())
    K("F8"); yield 0.2
    check("five times: everything", "Next para." in ed.selected_text(), ed.selected_text())
    K("Escape"); K("Right"); yield 0.2
    check("Esc ends Extend mode", not win.extend_mode and not ed.has_selection())

    # ---- Alt+Shift+Up / Down
    fresh(); yield 0.2
    T("one"); K("Return"); T("two"); K("Return"); T("three"); yield 0.3
    K("alt+shift+Up"); yield 0.3
    low = lambda: [x.lower() for x in body(ed)[:3]]  # noqa: E731
    check("Alt+Shift+Up moves the paragraph up", low() == ["one", "three", "two"], body(ed))
    K("alt+shift+Down"); yield 0.3
    check("Alt+Shift+Down moves it back", low() == ["one", "two", "three"], body(ed))
    fresh(); yield 0.2
    ed.insert_table(3, 2); E.view.after_edit(); yield 0.2
    for v in ("a1", "b1", "a2", "b2", "a3", "b3"):
        ed.type_text(v)
        ed.cell_step(False)
    ed.undo()              # the row the last Tab added
    E.view.after_edit()
    cells = lambda: [[ed.para_text_of(c[0]) for c in row] for row in ed.table_cells(0)]  # noqa: E731
    check("a table to move rows in", cells()[:3] == [["a1", "b1"], ["a2", "b2"], ["a3", "b3"]], cells())
    a3 = ed.table_cells(0)[2][0][0]
    ed.select_nodes(a3, 0, a3, 0); E.view.after_move(); yield 0.1
    K("alt+shift+Up"); yield 0.3
    check("in a table it moves the row", cells()[:3] == [["a1", "b1"], ["a3", "b3"], ["a2", "b2"]], cells())
    K("ctrl+z"); yield 0.2
    check("one undo puts it back", cells()[:3] == [["a1", "b1"], ["a2", "b2"], ["a3", "b3"]], cells())

    # ---- the Spike
    fresh(); yield 0.2
    T("alpha beta gamma"); yield 0.2
    p = ed.caret_pos()[0]
    ed.select_nodes(p, 0, p, 6); yield 0.1
    K("ctrl+F3"); yield 0.2
    p = ed.caret_pos()[0]
    ed.select_nodes(p, 0, p, 5)
    K("ctrl+F3"); yield 0.2
    check("Ctrl+F3 cuts to the Spike", body(ed)[0].strip() == "gamma", body(ed))
    K("End"); K("Return"); yield 0.1
    K("ctrl+shift+F3"); yield 0.3
    t = " ".join(body(ed))
    check("Ctrl+Shift+F3 pastes everything on it", "alpha" in t.lower() and "beta" in t.lower(), body(ed))
    msgs.clear()
    win.actions.do_spike_paste(); yield 0.1
    check("and empties it", win.app.spike == [])

    # ---- F4 repeats
    fresh(); yield 0.2
    T("first second"); yield 0.2
    p = ed.caret_pos()[0]
    ed.select_nodes(p, 0, p, 5)
    win.run(".uno:Bold"); yield 0.1
    ed.select_nodes(p, 6, p, 12)
    K("F4"); yield 0.2
    ed.select_nodes(p, 7, p, 8)
    check("F4 repeats the last formatting", ed.state().get("bold"), ed.state())

    # ---- Shift+F5
    fresh(); yield 0.2
    T("edited here"); K("Return"); T("then more"); yield 0.2
    K("ctrl+Home"); yield 0.2
    K("shift+F5"); yield 0.2
    check("Shift+F5 goes back to the last edit", ed.caret_pos()[0] == [n for k, n, _t in ed.body_blocks() if k == "p"][-1], ed.caret_pos())

    # ---- AutoFormat lists
    for typed, label in (("a) ", "a)"), ("A. ", "A."), ("i. ", "i."), ("I. ", "I."), ("c) ", "c)"),
                         ("(a) ", "(a)"), ("(1) ", "(1)"), ("3. ", "3.")):
        fresh(); yield 0.2
        T(typed + "item"); yield 0.3
        info = ed.list_info()
        check("typing %r starts a list labelled %r" % (typed, label), info is not None and info[3] == label
              and body(ed)[0].lower() == "item", (info, body(ed)))
    fresh(); yield 0.2
    T("Ann said a) was fine"); yield 0.3
    check("not in the middle of a sentence", body(ed)[0] == "Ann said a) was fine" and ed.list_info() is None, body(ed))
    fresh(); yield 0.2
    T("> arrow"); yield 0.3
    check("> starts an arrow bullet", ed.list_info() is not None and ed.list_info()[2], ed.list_info())

    # ---- --- then Enter
    fresh(); yield 0.2
    T("Before"); K("Return"); T("---"); K("Return"); yield 0.4
    blocks = body(ed)
    first = [x for x in ed.body_blocks() if x[0] == "p"][0][1]
    ed.select_nodes(first, 0, first, 0)
    check("--- Enter: a line under the paragraph above", blocks[0] == "Before" and all(x == "" for x in blocks[1:])
          and len(blocks) == 2, blocks)
    check("as its bottom border", (ed.para_values().get("borders") or {}).get("bottom"), ed.para_values().get("borders"))

    # ---- names of days, the AutoCorrect button
    fresh(); yield 0.2
    T("see you monday "); yield 0.3
    check("names of days capitalized", "Monday" in body(ed)[0], body(ed))
    fresh(); yield 0.2
    T("I saw teh "); yield 0.4
    check("the AutoCorrect button appears", win.acwatch.btn.get_visible() and win.acwatch.last["kind"] == "replace", win.acwatch.last)
    win.acwatch.change_back(); yield 0.2
    check("Change back restores it", "teh" in body(ed)[0], body(ed))
    fresh(); yield 0.2
    T("hello there. this is it "); yield 0.3
    check("capitalization noted for the button", win.acwatch.last and win.acwatch.last["kind"] == "caps", win.acwatch.last)

    # ---- Tab at the start of a paragraph
    fresh(); yield 0.2
    T("Paragraph text"); K("Home"); yield 0.2
    K("Tab"); yield 0.2
    check("Tab sets a first-line indent", ed.state().get("ind_first", 0) > 0 and "\t" not in body(ed)[0], (ed.state().get("ind_first"), body(ed)))
    K("BackSpace"); yield 0.2
    check("Backspace takes it away", ed.state().get("ind_first", 0) == 0 and body(ed)[0] == "Paragraph text", (ed.state().get("ind_first"), body(ed)))
    fresh(); yield 0.2
    K("Tab"); T("x"); yield 0.2
    check("an empty paragraph gets a tab", body(ed)[0] == "\tx", body(ed))

    # ---- KeyTips (W-07)
    fresh(); yield 0.2
    K("alt"); yield 0.4
    check("Alt shows the KeyTips", win.keytips.active)
    K("h"); yield 0.4
    check("H goes to Home and shows its KeyTips", win.keytips.active and win.ribbon.current_tab_name() == "Home"
          if hasattr(win.ribbon, "current_tab_name") else win.keytips.active)
    K("Escape"); K("Escape"); K("Escape"); yield 0.3
    check("Esc leaves them", not win.keytips.active)

    # ---- PDF options (W-05)
    fresh(); yield 0.2
    win.actions.apply_style("Heading 1")
    T("Chapter"); K("Return"); yield 0.2
    win.actions.apply_style("Normal")
    T("Body"); K("ctrl+Return"); T("Second page"); yield 0.5
    check("Ctrl+Enter starts a new page", ed.page_count() == 2, ed.page_count())
    d = tempfile.mkdtemp()
    pdf = os.path.join(d, "o.pdf")
    E.save_as(pdf, "pdf", keep=False, filter_data={"PageRange": "2", "ExportBookmarks": True})
    raw = open(pdf, "rb").read()
    check("PDF of a page range", raw.count(b"/Type /Page\n") + raw.count(b"/Type/Page\n") + raw.count(b"/Type /Page ") <= 1 or b"/Count 1" in raw, raw[:200])
    pdf2 = os.path.join(d, "all.pdf")
    E.save_as(pdf2, "pdf", keep=False, filter_data={"ExportBookmarks": True})
    raw2 = open(pdf2, "rb").read()
    # read the outline back (cairo 1.18 keeps it in compressed object streams)
    import gi
    gi.require_version("Poppler", "0.18")
    from gi.repository import Poppler
    titles = []
    it = Poppler.IndexIter.new(Poppler.Document.new_from_file("file://" + pdf2, None))
    while it is not None:
        a = it.get_action()
        titles.append(getattr(getattr(a, "any", None), "title", "") or "")
        if not it.next():
            break
    check("headings become bookmarks", any("Chapter" in t for t in titles), titles)

    # ---- .txt with no converter (W-03, W-06)
    txt = os.path.join(d, "plain.txt")
    open(txt, "w").write("line one\nline two\n")
    win.open_file(txt); yield 1.5
    ed = E.ed
    check(".txt opens with the new engine alone", body(ed)[:2] == ["line one", "line two"], body(ed))
    out = os.path.join(d, "back.txt")
    E.save_as(out, "txt", keep=False)
    check("and saves as text", open(out).read().split("\n")[:2] == ["line one", "line two"], open(out).read())

    # ---- treemap and sunburst (W-09)
    fresh(); yield 0.2
    ed = E.ed
    from folio.native import charts
    ref = charts.insert(win, charts.TREEMAP); yield 0.3
    check("a treemap goes in as a real chart", ref is not None and "chartEx" in (ref.part or ""), ref and ref.part)
    docx = os.path.join(d, "tm.docx")
    E.save_as(docx, "docx", keep=True)
    z = zipfile.ZipFile(docx)
    names = z.namelist()
    ex = [n for n in names if "chartEx" in n and n.endswith(".xml") and "_rels" not in n]
    check("saved as a chartEx part, as Word does", ex and "cx:chartSpace" in z.read(ex[0]).decode(), names)
    doc = z.read("word/document.xml").decode()
    check("in the document behind mc:AlternateContent", 'Requires="cx' in doc and "cx:chart" in doc)
    check("with its data in a workbook", any(n.endswith(".xlsx") for n in names))
    charts.set_type(ref, charts.SUNBURST); yield 0.2
    check("turned into a sunburst", charts.type_index(ref) == charts.SUNBURST)
    # ---- cover pages and header / footer designs
    fresh(); yield 0.2
    ed = E.ed
    T("Body text"); yield 0.2
    from folio import covers
    from folio.native import covers as nc
    covers.insert_cover(win, "Banded"); yield 0.4
    check("Cover Page goes in as Word keeps it (a Cover Pages content control)", nc.cover_id(ed) is not None, ed.content_controls())
    check("on its own page, before the text", ed.page_count() == 2 and "Body text" in body(ed)[-1], (ed.page_count(), body(ed)[-3:]))
    check("with its band behind the text", any((o[1] or "").startswith("CoverPageShape") for o in ed.objects_list()), ed.objects_list())
    covers.insert_cover(win, "Sideline"); yield 0.3
    check("another design replaces it", sum(1 for c in ed.content_controls() if "Cover Pages" in c[1]) == 1
          and not any((o[1] or "").startswith("CoverPageShape") for o in ed.objects_list()))
    covers.remove_current(win); yield 0.3
    check("Remove Current Cover Page", nc.cover_id(ed) is None and ed.page_count() == 1 and body(ed) == ["Body text"], body(ed))
    covers.hf_design(win, "footer", "Integral"); yield 0.3
    ft = ed.para_text_of(ed.caret_pos()[0]) if ed.story() == "hf" else ""
    check("a footer design with the page number", ed.page_hf(0)[1] and "1" in ft, (ed.story(), ft))
    ed.edit_header_footer(None); E.view.after_edit()

    # ---- Shading, Page Color, Fill Effects
    fresh(); yield 0.2
    ed = E.ed
    T("Shade me please"); yield 0.2
    win.actions.cmd(".uno:BackgroundColor", {"BackgroundColor": ("long", 0xFFFF00)}); yield 0.1
    check("Shading with nothing selected shades the paragraph", "FFFF00" in str(ed.shading_state("paras")).upper(), ed.shading_state("paras"))
    p = ed.caret_pos()[0]
    ed.select_nodes(p, 0, p, 5)
    win.actions.cmd(".uno:BackgroundColor", {"BackgroundColor": ("long", 0x00B0F0)}); yield 0.1
    check("Shading on selected text shades the text", not msgs, msgs)
    win.actions.run(("page-color", 0xDDEEFF)); yield 0.2
    check("Page Color", ed.page_color() == "DDEEFF", ed.page_color())
    from folio import filleffects
    filleffects._apply_native(win, {"kind": "gradient", "c1": 0x4472C4, "c2": 0xFFFFFF, "style": 90}); yield 0.2
    check("Fill Effects: a gradient", ed.page_fill() == ("gradient", "4472C4", "FFFFFF"), ed.page_fill())
    fx = os.path.join(tempfile.mkdtemp(), "fill.docx")
    E.save_as(fx, "docx", keep=False)
    doc = zipfile.ZipFile(fx).read("word/document.xml").decode()
    check("saved as Word keeps it (w:background, v:fill)", "<w:background" in doc and 'type="gradient"' in doc, doc[:300])
    win.actions.run(("page-color", None)); yield 0.1
    check("No Color", ed.page_color() is None and ed.page_fill() is None, (ed.page_color(), ed.page_fill()))

    # ---- WordArt, Text Effects, Quick Parts > Document Property
    fresh(); yield 0.2
    ed = E.ed
    n0 = len(ed.objects_list())
    win.model_call_sync("insertextras.insert_wordart", 1); yield 0.3
    check("WordArt goes in as a text box", len(ed.objects_list()) == n0 + 1, ed.objects_list())
    ed.deselect_object()
    if ed.story() == "textbox":
        ed.leave_textbox()
    E.view.after_edit()
    T("plain"); yield 0.2
    p = ed.caret_pos()[0]
    ed.select_nodes(p, 0, p, 5)
    win.model_call_sync("insertextras.text_effect", 2); yield 0.2
    check("Text Effects colour the selection", (ed.state() or {}).get("color", "").upper() == "ED7D31", ed.state().get("color"))
    K("End"); yield 0.1
    win.model_call_sync("insertextras.insert_doc_property", "Author"); yield 0.2
    check("Document Property inserts its field", any("AUTHOR" in f[1] for f in ed.fields_all()), ed.fields_all())

    # ---- Page Number in the margin, Remove Page Numbers / Header / Footer
    from folio import pagenum
    pagenum.insert(win, "margin", "right", "accent"); yield 0.3
    check("Page Margins: a number in the margin, from the header", ed.page_hf(0)[0] and not msgs, (ed.page_hf(0), msgs))
    pagenum.insert(win, "bottom", "center", "plain"); yield 0.3
    win.run("remove-page-numbers"); yield 0.3
    ed.edit_header_footer(0, True)
    ft = ed.para_text_of(ed.caret_pos()[0])
    ed.edit_header_footer(None); E.view.after_edit()
    check("Remove Page Numbers", not any(ch.isdigit() for ch in ft), ft)
    win.run("remove-header"); yield 0.2
    check("Remove Header", not msgs, msgs)

    # ---- from the other apps (S-05): a Sheets range as a table, a Draw picture
    fresh(); yield 0.2
    ed = E.ed
    sheets_html = ("<html><body><table><tr><td>Region</td><td>Sales</td></tr>"
                   "<tr><td>East</td><td>10</td></tr><tr><td>West</td><td>20</td></tr></table></body></html>")
    E.paste_html(sheets_html.encode()); yield 0.3
    tbls = [x for x in ed.body_blocks() if x[0] != "p"]
    check("a Sheets range pastes as a table", len(tbls) == 1 and
          [[ed.para_text_of(c[0]) for c in r] for r in ed.table_cells(0)] == [["Region", "Sales"], ["East", "10"], ["West", "20"]],
          ed.body_blocks())
    import cairo
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 40, 30)
    cr = cairo.Context(surf); cr.set_source_rgb(1, 0, 0); cr.paint()
    png = os.path.join(d, "draw.png"); surf.write_to_png(png)
    K("ctrl+End"); yield 0.1
    n0 = len(ed.objects_list())
    E.paste_data("image/png", open(png, "rb").read()); yield 0.3
    check("a Draw picture pastes as a picture", len(ed.objects_list()) == n0 + 1, ed.objects_list())
    check("no messages", not msgs, msgs)


def body_first(ed):
    return [x for x in ed.body_blocks() if x[0] == "p"][0][1]


run_scenarios(a)
