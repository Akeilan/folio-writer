exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
from folio import tocdlg
def idx_text(kind):
    ix = M().getDocumentIndexes()
    for i in range(ix.getCount()):
        x = ix.getByIndex(i)
        if x.supportsService(kind):
            return x, x.getAnchor().getString()
    return None, ""
def toc():
    fresh(); yield 0.3
    T("\nAlpha\nBeta\nGamma"); yield 0.5
    for i, st in ((2, "Heading 1"), (3, "Heading 2"), (4, "Heading 1")):
        p = paras()[i-1]; p.ParaStyleName = st
    K("ctrl+Home"); yield 0.3
    GLib.idle_add(lambda: (win.dialogs.toc_dialog(), False)[1]); yield 1.2
    d = dlg("Table of Contents")
    check("TOC dialog", bool(d))
    shot("l5_toc")
    labs = [w.get_label() for w in find_widget(d[0], lambda w: isinstance(w, Gtk.CheckButton))]
    check("TOC checkboxes", all(any(x in (l or "") for l in labs) for x in ("Show page numbers", "Right align", "hyperlinks")), labs)
    btns = [w.get_label() for w in find_widget(d[0], lambda w: isinstance(w, Gtk.Button) and not isinstance(w, Gtk.CheckButton))]
    check("Options and Modify", "_Options..." in btns and "_Modify..." in btns, btns)
    cb = [w for w in find_widget(d[0], lambda w: isinstance(w, Gtk.ComboBoxText))]
    cb[0].set_active(2)   # dashes
    respond("Table of Contents"); yield 1.5
    x, t = idx_text("com.sun.star.text.ContentIndex")
    note("toc text", repr(t))
    check("TOC inserted with entries", "Alpha" in t and "Beta" in t and "Gamma" in t, t)
    toks = [{p.Name: p.Value for p in tk} for tk in x.LevelFormat.getByIndex(1)]
    check("dash leader", any(tk.get("TabStopFillCharacter") == "-" for tk in toks), toks)
    # reopen: replaces the same TOC
    GLib.idle_add(lambda: (win.dialogs.toc_dialog(), False)[1]); yield 1.2
    d = dlg("Table of Contents")
    for w in find_widget(d[0], lambda w: isinstance(w, Gtk.CheckButton)):
        if "Show page numbers" in (w.get_label() or ""): w.set_active(False)
    respond("Table of Contents"); yield 1.5
    check("one TOC only", len(tocdlg.docapi.tocs(M())) == 1)
    x, t = idx_text("com.sun.star.text.ContentIndex")
    check("no page numbers", not any(ch.isdigit() for ch in t), repr(t))
    # options dialog
    GLib.idle_add(lambda: (win.dialogs.toc_dialog(), False)[1]); yield 1.2
    d = dlg("Table of Contents")
    ob = [w for w in find_widget(d[0], lambda w: isinstance(w, Gtk.Button) and w.get_label() == "_Options...")][0]
    GLib.idle_add(lambda: (ob.clicked(), False)[1]); yield 1.2
    check("TOC Options dialog", bool(dlg("Table of Contents Options")))
    shot("l5_tocopt")
    respond("Table of Contents Options", Gtk.ResponseType.CANCEL); yield 0.5
    respond("Table of Contents", Gtk.ResponseType.CANCEL); yield 0.5
def tof():
    fresh(); yield 0.3
    T("x"); yield 0.3
    docapi.insert_caption(M(), "Figure", "First picture"); yield 0.5
    K("ctrl+End"); T("\n"); yield 0.2
    docapi.insert_caption(M(), "Figure", "Second picture"); yield 0.5
    K("ctrl+Home"); T("\n"); K("ctrl+Home"); yield 0.3
    GLib.idle_add(lambda: (win.dialogs.table_of_figures(), False)[1]); yield 1.2
    d = dlg("Table of Figures")
    check("TOF dialog", bool(d))
    shot("l5_tof")
    respond("Table of Figures"); yield 1.5
    close_dialogs(); yield 0.3
    x, t = idx_text("com.sun.star.text.IllustrationsIndex")
    note("tof", repr(t))
    check("TOF has entries", "First picture" in t and "Second picture" in t, t)
def index():
    fresh(); yield 0.3
    T("apple banana cherry"); yield 0.3
    K("ctrl+Home"); K("ctrl+shift+Right"); yield 0.3
    docapi.mark_index_entry(M(), "Apple"); yield 0.3
    K("ctrl+End"); T("\n"); yield 0.3
    GLib.idle_add(lambda: (win.dialogs.insert_index(), False)[1]); yield 1.2
    d = dlg("Index")
    check("Index dialog", bool(d))
    shot("l5_index")
    btns = [w.get_label() for w in find_widget(d[0], lambda w: isinstance(w, Gtk.Button))]
    check("Index buttons", all(x in btns for x in ("Mar_k Entry...", "A_utoMark...", "_Modify...")), btns)
    for w in find_widget(d[0], lambda w: isinstance(w, Gtk.CheckButton)):
        if "Right align" in (w.get_label() or ""): w.set_active(True)
    respond("Index"); yield 1.5
    x, t = idx_text("com.sun.star.text.DocumentIndex")
    note("index", repr(t))
    check("Index has entry", "Apple" in t, t)
run_scenarios(toc, tof, index)
