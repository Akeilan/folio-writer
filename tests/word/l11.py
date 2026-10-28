exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
from folio import covers
from folio.native import covers as NC
def cover():
    fresh(); yield 0.3
    set_text("Body text"); yield 0.5
    for n in ("Ion (Dark)", "Sideline", "Retrospect"):
        covers.insert_cover(win, n); yield 1.0
        shot("l11_" + n.split()[0].lower())
    check("one cover page", NC.cover_id(E.ed) is not None and text().count("Document title") == 1, text()[:120])
    check("body kept", "Body text" in text())
    covers.remove_current(win); yield 0.8
    check("cover removed", "Document title" not in text() and "Body text" in text(), repr(text()[:80]))
    check("band removed", not any(o[1].startswith("CoverPage") for o in objects()), objects())
def hf():
    fresh(); yield 0.3
    T("x"); yield 0.3
    for n in covers.HEADERS:
        covers.hf_design(win, "header", n); yield 0.2
    note("headers", parts_text("word/header"))
    covers.hf_design(win, "footer", "Integral"); yield 0.6
    fx = parts_xml("word/footer")
    check("footer design", footer_on() and ("w:ptab" in fx or "<w:tab/>" in fx or "<w:tab />" in fx), (footer_on(), parts_text("word/footer"), fx[-400:]))
    covers.hf_design(win, "header", "Blank (Three Columns)"); yield 0.6
    check("three columns", any(h.count("[Type here]") == 3 for h in parts_text("word/header")), parts_text("word/header"))
    win.focus_document(); yield 0.5
    shot("l11_hf")
    c = find_control("Insert", "Header")
    pop = c.menu()
    labs = [w.get_label() for w in find_widget(pop, lambda w: isinstance(w, Gtk.Label))]
    check("header menu", "Save Selection to Header Gallery..." in labs and "Banded" in labs, labs)
run_scenarios(cover, hf)
