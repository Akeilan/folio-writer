exec(open("/home/claude/folio2/tests/common.py").read())
from folio import docapi
m = lambda: win.engine.model
def s0(): win.unmaximize(); win.resize(1590, 960); win.move(0,0)
def s1(): win.actions.insert_text("First section text. Figure here.")
def s2():
    docapi.insert_caption(m(), "Figure", "A caption")
    win.actions.insert_text("Second paragraph apple.")
def s3():
    n = docapi.insert_section_break(m(), "next-page"); log("sb", n, docapi.page_setup(m())["name"])
    docapi.set_page(m(), landscape=True); win.actions.insert_text("Landscape section apple.")
def s4():
    sec = docapi.insert_section_break(m(), "continuous"); log("cont", sec.Name)
    docapi.set_columns(m(), 2); win.actions.insert_text("Two column text " * 30)
    log("sec cols", docapi.view_cursor(m()).TextSection.TextColumns.getColumnCount(),
        "page cols", docapi.page_setup(m())["columns"])
def s5():
    log("tff"); docapi.insert_text_from_file(m(), "/tmp/ins.txt"); log("tff ok")
def s5b():
    vc = docapi.view_cursor(m()); vc.gotoStart(False); vc.goRight(5, True)
    docapi.mark_index_entry(m(), None); log('mark ok')
    vc.gotoEnd(False)
    docapi.insert_table_of_figures(m(), "Figure"); log("tof ok")
    docapi.insert_index(m()); log("idx ok")
    win.run_window_action("language-dialog") if False else None
    docapi.set_language(m(), "en", "GB")
    log("lang", docapi.current_language(m()))
    t = m().getText().getString()
    log("has inserted", "Inserted line" in t, "figure toc", "A caption" in t.split("apple.")[-1])
    ix = m().getDocumentIndexes(); log("indexes", [ix.getByIndex(i).getImplementationName() for i in range(ix.getCount())])
    ix=m().getDocumentIndexes(); [log("ix", i, repr(ix.getByIndex(i).getAnchor().getString()[:80])) for i in range(ix.getCount())]
    log("pages", win.engine.view.get_parts() if hasattr(win.engine.view,"get_parts") else "?")
def s6(): shot("sections"); win.actions.do_undo(); log("undo ok")
def s7(): app.quit()
steps(s0, s1, s2, s3, s4, s5, s5b, s6, s7, delay=1800)
