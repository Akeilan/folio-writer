exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
from folio import findopts
def _sd(t):
    sd = M().createSearchDescriptor(); sd.SearchString = t; return sd
def open_fr(tab=0):
    GLib.idle_add(lambda: (win.dialogs.find_replace(tab), False)[1])
def st(): return win.dialogs._fr
def setfind(t):
    st()["dlg"]; 
    for e in find_widget(st()["dlg"], lambda w: isinstance(w, Gtk.ComboBoxText) and w.get_has_entry()):
        pass
    combos = find_widget(st()["dlg"], lambda w: isinstance(w, Gtk.ComboBoxText) and w.get_has_entry())
    combos[0].get_child().set_text(t)
def click(label):
    b = [w for w in find_widget(st()["dlg"], lambda w: isinstance(w, Gtk.Button) and (w.get_label() or "").replace("_", "") == label)]
    GLib.idle_add(lambda: (b[0].clicked(), False)[1])
def reset():
    for b in st()["checks"].values(): b.set_active(False)
def opts():
    fresh(); yield 0.3
    T("Mr Smyth went to see Smith. They ran fast; he runs daily. Preview the reviewer. e-mail email "); yield 0.5
    K("ctrl+Home"); yield 0.3
    open_fr(0); yield 1.0
    click("More >>"); yield 0.5
    shot("l6_more")
    labs = [w.get_label().replace("_", "") for w in find_widget(st()["dlg"], lambda w: isinstance(w, Gtk.CheckButton))]
    check("More options present", all(x in labs for x in ("Sounds like (English)", "Find all word forms (English)", "Match prefix", "Match suffix", "Ignore punctuation characters", "Ignore white-space characters")), labs)
    st()["checks"]["sounds"].set_active(True); setfind("Smith"); yield 0.2
    click("Find Next"); yield 0.6
    check("Sounds like finds Smyth", sel() == "Smyth", sel())
    reset(); st()["checks"]["forms"].set_active(True); setfind("run"); yield 0.2
    click("Find Next"); yield 0.6
    check("word forms finds ran", sel() == "ran", sel())
    click("Find Next"); yield 0.6
    check("word forms finds runs", sel() == "runs", sel())
    reset(); st()["checks"]["prefix"].set_active(True); setfind("view"); yield 0.2
    K("ctrl+Home"); yield 0.2
    click("Find Next"); yield 0.6
    v1 = vc().getStart()
    note("prefix sel", sel())
    reset(); st()["checks"]["suffix"].set_active(True); setfind("view"); yield 0.2
    click("Find Next"); yield 0.6
    check("suffix finds Preview's view", sel() == "view", sel())
    reset(); st()["checks"]["ign_punct"].set_active(True); setfind("email"); yield 0.2
    K("ctrl+Home"); yield 0.2
    click("Find Next"); yield 0.6
    check("ignore punctuation finds e-mail", (sel() or "").lower() == "e-mail", sel())
    reset()
    # reading highlight
    setfind("the"); yield 0.2
    was = M().isModified()
    GLib.idle_add(lambda: (win.reading_hl.highlight([M().getText().getStart()]) and False))
    yield 0.3
    win.reading_hl.clear()
    hl = [w for w in find_widget(st()["dlg"], lambda w: isinstance(w, Gtk.MenuButton) and "Highlight" in (w.get_label() or "").replace("_", ""))]
    check("Reading Highlight button", bool(hl))
    items = hl[0].get_popup().get_children()
    GLib.idle_add(lambda: (items[0].activate(), False)[1]); yield 0.8
    shot("l6_hl")
    check("highlight marks", len(win.reading_hl.marks) >= 2, len(win.reading_hl.marks))
    check("highlight not a change", M().isModified() == was, (was, M().isModified()))
    GLib.idle_add(lambda: (items[1].activate(), False)[1]); yield 0.5
    check("cleared", not win.reading_hl.marks)
    # find in main document
    fi = [w for w in find_widget(st()["dlg"], lambda w: isinstance(w, Gtk.MenuButton) and "Find In" in (w.get_label() or "").replace("_", ""))]
    GLib.idle_add(lambda: (fi[0].get_popup().get_children()[0].activate(), False)[1]); yield 0.8
    cnt = docapi.controller(M()).getSelection().getCount()
    check("Find In selects all", cnt >= 2, cnt)
def fmt():
    if getattr(win.dialogs, "_fr", None): win.dialogs._fr["dlg"].destroy()
    close_dialogs(); yield 0.3
    fresh(); yield 0.3
    T("plain bold plain bold"); yield 0.3
    r = M().findAll(_sd("bold"))
    for i in range(r.getCount()): r.getByIndex(i).CharWeight = 150.0
    open_fr(0); yield 1.0
    st()["ffmt"].clear(); st()["ffmt"].attrs["CharWeight"] = 150.0; st()["ffmt"].words.append("Bold")
    setfind("bold"); K("ctrl+Home"); yield 0.3
    click("Find Next"); yield 0.6
    check("find with format", sel() and sel().strip() == "bold", sel())
    setfind("plain"); yield 0.2
    st()["ffmt"].clear()
    rf = st()["rfmt"]; rf.clear(); rf.attrs["CharPosture"] = findopts.bridge.enum("com.sun.star.awt.FontSlant", "ITALIC"); rf.words.append("Italic")
    nb = st()["nb"]; nb.set_current_page(1); yield 0.4
    click("Replace All"); yield 1.0
    close_dialogs_msgs = [d for d in dialogs_open() if isinstance(d, Gtk.MessageDialog)]
    for d in close_dialogs_msgs: d.response(Gtk.ResponseType.OK)
    yield 0.3
    p = paras()[0]; c = p.getText().createTextCursorByRange(p.getStart()); c.goRight(3, True)
    check("replace format applied, text kept", c.CharPosture.value == "ITALIC" and text().lower().startswith("plain"), (c.CharPosture.value, text()))
    rf.clear()
    st()["dlg"].destroy(); yield 0.4
def goto():
    close_dialogs(); yield 0.3
    fresh(); win.present(); win.focus_document(); yield 0.6
    T("one\ntwo\nthree"); yield 0.3
    note("before break", para_texts()); yield 1.0
    note("before break2", para_texts())
    docapi.insert_section_break(M(), "next-page"); yield 0.5
    T("four"); yield 0.3
    K("ctrl+Home"); yield 0.3
    open_fr(2); yield 1.0
    from folio.widgets import list_selected
    tv = [w for w in find_widget(st()["dlg"], lambda w: isinstance(w, Gtk.TreeView))][0]
    tv.get_selection().select_path(Gtk.TreePath(1)); yield 0.3
    combos = find_widget(st()["dlg"], lambda w: isinstance(w, Gtk.ComboBoxText) and w.get_has_entry())
    combos[-1].get_child().set_text("2"); yield 0.2
    combos[-1].get_child().activate(); yield 0.6
    check("Go To section 2", vc().getPage() == 2, vc().getPage())
    tv.get_selection().select_path(Gtk.TreePath(2)); yield 0.3
    note("paras", para_texts())
    combos[-1].get_child().set_text("3"); combos[-1].get_child().activate(); yield 0.6
    c = vc().getText().createTextCursorByRange(vc().getStart()); c.gotoEndOfParagraph(True)
    check("Go To line 3", c.getString() == "three", c.getString())
    st()["dlg"].destroy()
run_scenarios(opts, fmt, goto)
