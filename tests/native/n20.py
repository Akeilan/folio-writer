exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
import zipfile
def a():
    yield 1.0
    focus(); yield 0.2
    ed = E.ed
    win.dialogs.message = lambda *a, **k: None
    for i in range(60):
        ed.type_text("Paragraph %d has internationalization considerations notwithstanding extraordinarily comprehensive documentation.\n" % i)
    E.view.after_edit(); yield 0.3
    ed.move_caret("doc_start", False); E.view.after_move()
    win.actions.run(("line-numbers", "continuous")); yield 0.3
    check("line numbers on", ed.line_numbers() is not None and ed.line_numbers()[0] == "continuous", ed.line_numbers())
    win.actions.run(("hyphenation", True)); yield 0.3
    check("hyphenation on", ed.setting("autoHyphenation"))
    win.actions.run(("model", "drop_cap", "dropped")); yield 0.3
    check("drop cap", ed.drop_cap_info() is not None and ed.drop_cap_info()[0] == "drop", ed.drop_cap_info())
    win.actions.run(("watermark", "DRAFT")); yield 0.5
    check("watermark", ed.has_watermark())
    shot("n20")
    # odd/even headers: edit the even page's header
    E.command(".uno:JumpToHeader"); yield 0.4
    win.actions.hf_option("odd_even"); yield 0.4
    check("odd even on", ed.setting("evenAndOddHeaders"))
    pg = ed.story_page()
    check("first page is odd", ed.page_hf_kind(0) == 0)
    ed.edit_header_footer(None); E.view.document_changed()
    ed.goto("Page", "2"); E.view.after_move()
    E.command(".uno:JumpToHeader"); yield 0.4
    ed.type_text("Even header text"); E.view.after_edit(); yield 0.3
    check("even page header", ed.page_hf_kind(1) == 2 and ed.page_hf(1)[0])
    win.actions.run("close-header-footer"); yield 0.3
    win.save_to("/tmp/n20.docx"); yield 0.6
    z = zipfile.ZipFile("/tmp/n20.docx")
    d = z.read("word/document.xml").decode()
    st = z.read("word/settings.xml").decode()
    check("saved even ref", 'w:type="even"' in d)
    check("saved lnNumType", "w:lnNumType" in d and "w:dropCap" in d)
    check("saved settings", "w:autoHyphenation" in st and "w:evenAndOddHeaders" in st)
    hs = "".join(z.read(n).decode() for n in z.namelist() if "header" in n and n.endswith(".xml"))
    check("watermark in header", "PowerPlusWaterMarkObject" in hs and "Even header text" in hs)
    win.actions.run(("watermark", "")); yield 0.3
    check("watermark removed", not ed.has_watermark())
    win.actions.run(("line-numbers", "none")); yield 0.3
    check("line numbers off", ed.line_numbers() is None)
run_scenarios(a)
