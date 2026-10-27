exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
from folio import covers
def cover():
    fresh(); yield 0.3
    M().getText().setString("Body text"); yield 0.5
    for n in ("Ion (Dark)", "Sideline", "Retrospect"):
        covers.insert_cover(win, n); yield 1.0
        shot("l11_" + n.split()[0].lower())
    check("one cover page", M().getBookmarks().hasByName("_CoverPage") and text().count("Document title") == 1, text()[:120])
    check("body kept", "Body text" in text())
    covers.remove_cover(M()); yield 0.8
    check("cover removed", "Document title" not in text() and "Body text" in text(), repr(text()[:80]))
    dp = M().getDrawPage()
    check("band removed", not any((dp.getByIndex(i).Name or "").startswith("CoverPage") for i in range(dp.getCount())))
def hf():
    fresh(); yield 0.3
    T("x"); yield 0.3
    for n in covers.HEADERS:
        covers.hf_design(win, "header", n); yield 0.2
    ps = docapi.page_style(M())
    note("last header", ps.HeaderText.getString())
    covers.hf_design(win, "footer", "Integral"); yield 0.6
    check("footer design", ps.FooterIsOn and "\t" in ps.FooterText.getString(), repr(ps.FooterText.getString()))
    covers.hf_design(win, "header", "Blank (Three Columns)"); yield 0.6
    check("three columns", ps.HeaderText.getString().count("[Type here]") == 3, repr(ps.HeaderText.getString()))
    win.focus_document(); yield 0.5
    shot("l11_hf")
    c = find_control("Insert", "Header")
    pop = c.menu()
    labs = [w.get_label() for w in find_widget(pop, lambda w: isinstance(w, Gtk.Label))]
    check("header menu", "Save Selection to Header Gallery..." in labs and "Banded" in labs, labs)
run_scenarios(cover, hf)
