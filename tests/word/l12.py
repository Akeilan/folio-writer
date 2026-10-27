exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
from folio import insertmore as IM
def smart():
    fresh(); yield 0.3
    g = IM.insert_smartart(win, "process"); yield 1.0
    check("smartart inserted", IM.is_smartart(M(), g))
    IM.edit_graphic(win, g, "after"); yield 0.8
    g = [M().getDrawPage().getByIndex(i) for i in range(M().getDrawPage().getCount()) if IM.is_smartart(M(), M().getDrawPage().getByIndex(i))][0]
    info = IM.smartart_info(M(), g)
    check("Add Shape After", len(info["lines"]) == 4, info["lines"])
    IM.edit_graphic(win, g, "demote"); yield 0.8
    g = [M().getDrawPage().getByIndex(i) for i in range(M().getDrawPage().getCount()) if IM.is_smartart(M(), M().getDrawPage().getByIndex(i))][0]
    info = IM.smartart_info(M(), g)
    check("Demote", info["lines"][-1].startswith("\t"), info["lines"])
    IM.change_layout(win, g, "matrix", style=3); yield 0.8
    g = [M().getDrawPage().getByIndex(i) for i in range(M().getDrawPage().getCount()) if IM.is_smartart(M(), M().getDrawPage().getByIndex(i))][0]
    info = IM.smartart_info(M(), g)
    check("layout + style kept", info["layout"] == "matrix" and info.get("style") == 3, info)
    docapi.controller(M()).select(g); yield 0.8
    win.update_object_tabs(); yield 0.5
    tab = [t for t in win.ribbon.tabs if t.name == "SmartArt Design"][0]
    check("SmartArt Design tab shown", tab.button.get_visible())
    win.select_tab("SmartArt Design"); yield 0.6
    shot("l12_tab")
    labs = [_clean(getattr(c, "label", "") or "") or (c.tooltip_text or "") for c in win.ribbon.controls if getattr(c, "tab_name", "") == "SmartArt Design"]
    note("controls", labs)
    for x in ("Add Shape", "Promote", "Demote", "Move Up", "Move Down", "Reset Graphic", "Convert", "Styles"):
        check("control " + x, any(x == l or l.startswith(x) for l in labs), "")
    IM.convert_to_text(win, g); yield 1.5
    check("convert to text", "Text" in text() and not any(IM.is_smartart(M(), M().getDrawPage().getByIndex(i)) for i in range(M().getDrawPage().getCount())), repr(text()))
    GLib.idle_add(lambda: (IM.smartart_dialog(win), False)[1]); yield 1.0
    d = dlg("SmartArt")
    if d:
        labs = [w.get_text() for w in find_widget(d[0], lambda w: isinstance(w, Gtk.Label))]
        check("categories Matrix & Picture", "Matrix" in labs and "Picture" in labs and "All" in labs, labs)
        shot("l12_dlg")
    close_dialogs(); yield 0.4
run_scenarios(smart)
