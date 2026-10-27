exec(open("/home/claude/folio2/tests/common.py").read())
from folio import citations as C, dlg_cite
A = win.actions; m = lambda: win.engine.model; st = {}
def s0():
    win.unmaximize(); win.resize(1590,960); win.move(0,0); A.insert_text("Claim ")
    a = C.add_source(m(), {"type":"Book","author":"Smith, John","title":"The Art of Writing","year":"2020","city":"New York","publisher":"Penguin"}, master=True)
    C.insert_citation(m(), a["tag"])
def s1(): A.cmd(".uno:InsertPara"); C.insert_bibliography(m(), "Bibliography")
def s2(): log("saved", win.save_to("/tmp/cite.docx"))
def s3(): st["w"] = app.new_window("/tmp/cite.docx")
def s4():
    m2 = st["w"].engine.model
    log("reopen text", repr(m2.getText().getString()))
    log("sources", C.doc_sources(m2))
    st["w"].destroy() if False else None
    GLib.timeout_add(1500, lambda: (shot("srcmgr"), [w.response(Gtk.ResponseType.CLOSE) for w in Gtk.Window.list_toplevels() if isinstance(w, Gtk.Dialog) and w.get_visible()], False)[2])
    dlg_cite.manage_sources(win)
def s5():
    GLib.timeout_add(1500, lambda: (shot("srcdlg"), [w.response(Gtk.ResponseType.CANCEL) for w in Gtk.Window.list_toplevels() if isinstance(w, Gtk.Dialog) and w.get_visible()], False)[2])
    dlg_cite.source_dialog(win, {"type": "Journal Article"})
def s6(): app.quit()
steps(s0, s1, s2, s3, s4, s5, s6, delay=2500)
