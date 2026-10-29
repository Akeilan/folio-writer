import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
from folio.panes import NavigationPane
def nav():
    fresh(); yield 0.3
    T("cat dog cat"); yield 0.4
    K("ctrl+f"); yield 0.8; T("cat"); yield 1.2
    p = win.panes.get(NavigationPane)
    check("2 results", len(p._ranges) == 2, len(p._ranges))
    focus(); K("End"); T(" cat bird"); yield 2.0
    check("results refresh after typing", len(p._ranges) == 3, (len(p._ranges), p.rcount.get_text()))
    check("cursor stays where typing", pos().endswith("bird"), repr(pos()))
    K("Escape")
def ctx():
    fresh(); yield 0.3
    T("Alpha bravo charlie"); yield 0.4
    find("bravo").select(); yield 0.4
    GLib.idle_add(lambda: (win.dialogs.context_menu(None), False)[1]); yield 1.0
    labs = [l.replace("_", "") for l in menu_labels() if l]
    for w in popups():
        for mi in find_widget(w, lambda x: isinstance(x, Gtk.MenuItem)):
            for lab in find_widget(mi, lambda x: isinstance(x, Gtk.Label)):
                labs.append(lab.get_text())
    check("Search shows the selected word", any("bravo" in l and "Search" in l for l in labs), labs)
    check("no table items outside a table", not any("Merge Cells" in l or "Table Properties" in l for l in labs), labs)
    K("Escape"); yield 0.4
def status():
    win.open_file("/tmp/wfid/fid.docx"); yield 5.0
    caret_end(); yield 1.5
    lab = [w.get_label() for w in find_widget(win.status, lambda w: isinstance(w, Gtk.Button) and (w.get_label() or "").startswith("Page "))]
    check("status shows physical page", "Page 4 of 4" in lab, lab)
def tabname():
    labs = [t.button.get_label() for t in win.ribbon.tabs if t.contextual]
    check("table tab labeled Layout", "Layout" in labs and "Table Layout" not in labs, labs)
    yield 0.1
run_scenarios(nav, ctx, status, tabname)
