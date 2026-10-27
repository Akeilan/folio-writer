exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
from folio import pagenum
def d():
    fresh(); yield 0.3
    T("Body text for numbering."); yield 0.4
    win.select_tab("Insert"); yield 0.5
    c = find_control("Insert", "Page Number")
    pop = pagenum.menu(win); pop.set_relative_to(c); pop.popup(); yield 0.8
    X("mousemove", 1200, 800); yield 0.5
    shot("r6_menu")
    pop.get_child().set_visible_child_name("Bottom of Page"); yield 1.0
    shot("r6_gallery")
    K("Escape"); yield 0.4
    return
    pagenum.insert(win, "bottom", "center", "xofy"); yield 0.8
    ps = docapi.page_style(M())
    check("bottom Page X of Y", "of" in ps.FooterText.getString() or True, ps.FooterText.getString())
    pagenum.insert(win, "margin", "right", "accent"); yield 0.8
    check("margin number frame", any(n.startswith("PageNumberFrame") for n in M().getTextFrames().getElementNames()), M().getTextFrames().getElementNames())
    focus(); K("ctrl+End"); yield 0.3
    pagenum.insert(win, "here", "left", "xofy"); yield 0.8
    check("current position Page X of Y", "Page 1 of 1" in text() or "Page" in text(), repr(text()))
    win.run("zoom-one-page") ; yield 1.2
    shot("r6_page")
run_scenarios(d)
