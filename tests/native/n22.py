exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
# 2.26: page setup, borders and shading, HTML paste, spelling as you type, Editor pane,
# thesaurus, language, select similar, selection pane, list commands, text from file
import os
import zipfile
from gi.repository import Gtk


def doc_xml(path):
    return zipfile.ZipFile(path).read("word/document.xml").decode()


def a():
    yield 1.0
    focus(); yield 0.2
    ed = E.ed
    v = E.view
    msgs = []
    win.dialogs.message = lambda *a, **k: msgs.append(a)
    win.dialogs.confirm = lambda *a, **k: True
    check("the new engine is the default", getattr(E, "native", False))

    # ---- Page Setup
    from folio.native import pagesetup as NP
    info = NP.read(win)
    check("page setup reads the section", info["width"] > 20000 and info["top"] > 2000, info)
    v2 = dict(info, top=3810, bottom=3810, left=3175, right=3175, landscape=True, valign="CENTER",
              diff_first=True, header_edge=1000, gutter=635)
    NP.apply_to(win, v2, 1)
    yield 0.3
    ps = ed.page_setup(ed.current_section())
    check("margins, gutter and landscape applied", ps["width"] > ps["height"] and abs(ps["top"] - 2160) < 3
          and abs(ps["gutter"] - 360) < 3, ps)
    check("vertical alignment and first page", ps["v_align"] == "center" and ps["title_pg"], ps)
    ed.undo(); v.after_edit(); yield 0.2
    check("page setup undoes in one step", ed.page_setup(0)["width"] < ed.page_setup(0)["height"])

    # ---- text for the rest
    ed.type_text("Teh quick brown fox jumpd over the lazy dog.\nSecond paragraph is here.\nThird paragraph.")
    v.after_edit(); yield 0.3

    # ---- Borders and Shading (paragraph box + shading)
    from folio.native import borders
    from folio import bordersdlg
    ed.move_caret("doc_start", False); v.after_move()

    class D:
        pass
    d = D()
    win2 = Gtk.Window()
    st = {"setting": "box", "style": 3, "color": 0xC00000, "width": 1.5, "sides": set(bordersdlg.SIDES), "dist": {}}
    d.borders = bordersdlg.BorderPage(win2, False, ["Paragraph"], st["sides"], st)
    d.borders.touched = True
    d.borders.radios["shadow"].set_active(True)
    d.page = bordersdlg.BorderPage(win2, True, ["Whole document"], set(), {"setting": "none", "sides": set()})
    from folio.widgets import color_button, combo
    d.fill = color_button(0xFFFF99)
    d.pstyle = combo([n for n, _v in bordersdlg.PATTERNS], 0)
    d.pcolor = color_button(-1)
    d.sapply = combo(["Paragraph"], 0)
    d.nb = Gtk.Notebook()
    borders.apply(win, d, -1)
    yield 0.3
    bs = dict(ed.border_state("paras"))
    check("paragraph borders written", set(bs) >= {"top", "left", "bottom", "right"} and dict(bs["top"]).get("w:val") == "double"
          and dict(bs["top"]).get("w:shadow") == "1", bs)
    check("paragraph shading written", ed.shading_state("paras") == "FFFF99", ed.shading_state("paras"))
    st2 = borders._state(ed.border_state("paras"), lambda s: 0)
    check("the dialog reads them back", st2["setting"] == "shadow" and st2["style"] == 3 and abs(st2["width"] - 1.5) < 0.01, st2)

    # ---- spelling as you type
    sp = v.speller
    check("speller attached", sp is not None)
    v.typing = False
    sp.invalidate()
    v.queue_draw(); yield 0.2
    sp.page_marks(0)
    for _ in range(10):
        yield 0.1
    marks = sp.pages.get(0, (0, [], []))[1]
    words = [m[3] for m in marks]
    check("misspelled words are marked", "Teh" in words and "jumpd" in words and "quick" not in words, words)
    rects = sp.page_marks(0)
    check("with underlines under them", len(rects) >= 2 and all(r[2] > 0 for r in rects), rects[:3])
    hit = sp.at(0, rects[0][0] + 1, rects[0][1] + 1)
    check("a word found under the pointer", hit is not None and hit[3] in ("Teh", "jumpd"), hit)
    from folio.native import spell
    items = [it[0] for it in spell.menu_items(win, hit) if it]
    check("the menu offers suggestions, the closest first", items[:1] == ["The"], items)
    # Ignore All
    for it in spell.menu_items(win, hit):
        if it and it[0] == "Ignore All":
            it[1]()
    for _ in range(10):
        yield 0.1
    sp.page_marks(0)
    for _ in range(10):
        yield 0.1
    words = [m[3] for m in sp.pages.get(0, (0, [], []))[1]]
    check("Ignore All drops it", hit[3] not in words, words)

    # ---- Editor pane: next misspelling, change
    from folio.native import docops
    ed.move_caret("doc_start", False); v.after_move()
    w = docops.next_misspelling(win, False, win.ignored_words)
    check("Editor finds the next misspelling", w == "jumpd" and ed.selected_text() == "jumpd", (w, ed.selected_text()))
    docops.replace_selection(win, "jumped"); yield 0.2
    check("Change replaces it", "fox jumped over" in ed.selected_text() or "jumped" in docops.document_text(win))
    g = docops.next_grammar(win, False, set())
    check("grammar check runs", g is None or isinstance(g[0], str), g)
    win.run("spelling"); yield 0.5
    from folio.panes import EditorPane
    pane = win.panes.get(EditorPane)
    check("Spelling & Grammar opens the Editor pane", pane is not None and pane.get_parent() is not None)

    # ---- Thesaurus
    syn = docops.synonyms("happy")
    check("thesaurus finds synonyms", syn and any("glad" in " ".join(s) or "felicitous" in m for m, s in syn), syn[:2])
    win.run("thesaurus"); yield 0.4

    # ---- Language
    from folio.native import proofing
    ed.move_caret("doc_start", False); ed.move_caret("end", True); v.after_move()
    proofing.set_language(win, "fr", "FR"); yield 0.2
    check("language set on the text", ed.state()["lang"] == "fr-FR", ed.state()["lang"])
    proofing.set_language(win, "en", "US", no_proof=True); yield 0.2
    win.save_to("/tmp/n22a.docx"); yield 0.5
    x = doc_xml("/tmp/n22a.docx")
    check("noProof saved", "w:noProof" in x and 'w:lang w:val="en-US"' in x)

    # ---- HTML paste
    html_in = ("<html><body><!--StartFragment--><h1>Pasted Title</h1><p>Some <b>bold</b> and <i>italic</i> "
               "with a <a href='https://example.org'>link</a>.</p><ul><li>one</li><li>two</li></ul>"
               "<table><tr><th>A</th><th>B</th></tr><tr><td>1</td><td>2</td></tr></table><!--EndFragment--></body></html>")
    ed.move_caret("doc_end", False); ed.type_text("\n"); v.after_edit()
    ok = E.paste_html(html_in.encode()); yield 0.4
    win.save_to("/tmp/n22b.docx"); yield 0.5
    x = doc_xml("/tmp/n22b.docx")
    check("HTML pasted with its formatting", ok and "Pasted Title" in x and "<w:b/>" in x and "<w:i/>" in x)
    check("link pasted as a hyperlink", "HYPERLINK" in x and "example.org" in x)
    check("table pasted", "<w:tbl>" in x and ">A<" in x)
    check("heading style kept", 'w:pStyle w:val="Heading1"' in x, x[:200])

    # ---- Select similar formatting
    ed.move_caret("doc_start", False); v.after_move()
    sid = ed.para_style_id()
    n = ed.count_style_instances(sid)
    win.run(("select-similar")); yield 0.3
    rects = ed.selection_rects()
    check("Select All Text With Similar Formatting selects every one", n >= 3 and len(rects) >= 4, (n, len(rects)))
    ed.toggle("w:b"); v.after_edit(); yield 0.2
    win.save_to("/tmp/n22c.docx"); yield 0.5
    x = doc_xml("/tmp/n22c.docx")
    check("formatting goes to each selected stretch", x.count("<w:b/>") >= n, x.count("<w:b/>"))
    ed.undo(); v.after_edit()

    # ---- lists
    ed.move_caret("doc_end", False)
    ed.type_text("\nItem one\nItem two\nItem three\nItem four")
    v.after_edit(); yield 0.2
    ed.move_caret("up", False); ed.move_caret("up", False); ed.move_caret("up", True)
    ed.move_caret("up", True); ed.move_caret("down", True)
    for _ in range(4):
        pass
    # select the four items
    ed.move_caret("doc_end", False)
    for _ in range(3):
        ed.move_caret("up", True)
    ed.move_caret("home", True)
    win.actions.cmd(".uno:DefaultNumbering"); yield 0.3
    ed.move_caret("doc_end", False); ed.move_caret("up", False); v.after_move()
    info = ed.list_info()
    check("numbered list made", info is not None and not info[2] and info[3].startswith("3"), info)
    from folio import lists
    lists.restart_at(win.dialogs.model, 1); yield 0.3
    info = ed.list_info()
    check("Restart at 1", info is not None and info[3].startswith("1"), info)
    lists.continue_numbering(win.dialogs.model); yield 0.3
    info = ed.list_info()
    check("Continue Numbering", info is not None and info[3].startswith("3"), info)
    from folio.native import lists as NL
    NL.apply_numbering_value(win, True, False, 7); yield 0.3
    info = ed.list_info()
    check("Set Numbering Value", info is not None and info[3].startswith("7"), info)
    ed.undo(); v.after_edit(); yield 0.2
    cur = ed.list_level_indents()
    check("list indents read", cur is not None and cur[1] > cur[0], cur)
    ok = ed.set_list_level_indents(360, 1080, "space"); v.after_edit()
    check("Adjust List Indents", ok and ed.list_level_indents() == (360, 1080, "space"), ed.list_level_indents())
    ed.move_caret("doc_end", False)
    for _ in range(3):
        ed.move_caret("up", True)
    lists.apply_multilevel(win.dialogs.model, lists.MULTI[2][1]); yield 0.3
    ed.move_caret("doc_end", False); ed.move_caret("up", False); v.after_move()
    ed.change_list_level(1); v.after_edit(); yield 0.2
    info = ed.list_info()
    check("multilevel list: 1.1 style", info is not None and "." in info[3] and info[1] == 1, info)
    lists.heading_numbering(win.dialogs.model); yield 0.3
    win.save_to("/tmp/n22d.docx"); yield 0.5
    st = zipfile.ZipFile("/tmp/n22d.docx").read("word/styles.xml").decode()
    check("heading numbering links the Heading styles", st.count("<w:numPr>") >= 2, st.count("<w:numPr>"))

    # ---- selection pane
    from gi.repository import GdkPixbuf
    pb = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, 64, 48)
    pb.fill(0x3366CCFF)
    pic = "/tmp/n22pic.png"
    pb.savev(pic, "png", [], [])
    ed.move_caret("doc_end", False); ed.type_text("\n")
    from folio.native import objects
    objects.insert_picture_path(win, pic); yield 0.3
    ed.deselect_object()
    ed.insert_shape("rect", 0, 300, 300, 80, 50, "Rectangle", False); v.after_edit(); yield 0.2
    lst = ed.objects_list()
    check("objects listed", len(lst) == 2 and {k for _n, _m, k, _v in lst} == {"Picture", "Shape"}, lst)
    win.run("selection-pane"); yield 0.4
    from folio.native.selection import NativeSelectionPane
    sp2 = win.panes.get(NativeSelectionPane)
    check("Selection pane shows them", sp2 is not None and len(sp2.store) == 2)
    node = lst[0][0]
    ed.object_set_meta(node, visible=False); v.document_changed()
    check("hidden from the pane", not [x for x in ed.objects_list() if x[0] == node][0][3])
    ed.object_set_meta(node, name="Logo")
    check("renamed", [x for x in ed.objects_list() if x[0] == node][0][1] == "Logo")
    ok = ed.select_object_node(lst[1][0])
    check("selected from the pane", ok and ed.selected_object() is not None)
    ed.deselect_object()

    # ---- text from file
    from folio.native import insertfile
    ed.move_caret("doc_end", False); ed.type_text("\n")
    insertfile.insert(win, "/tmp/n22a.docx"); yield 0.4
    check("Text from File brings a document in", docops.document_text(win).count("quick brown fox") >= 2)
    with open("/tmp/n22.txt", "w") as f:
        f.write("Plain text file line.\n")
    insertfile.insert(win, "/tmp/n22.txt"); yield 0.3
    check("and a text file", "Plain text file line." in docops.document_text(win))
    shot("n22")
run_scenarios(a)
