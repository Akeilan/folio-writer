exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
from folio import lists
if NATIVE:
    from folio.native import lists as _nl
    _lm = lists
    class _L:
        MULTI = _lm.MULTI
        restart_at = staticmethod(lambda m, v=1: _nl.restart_at(win, v))
        continue_numbering = staticmethod(lambda m: _nl.continue_numbering(win))
        apply_multilevel = staticmethod(lambda m, lv: _nl.apply_multilevel(win, lv))
        heading_numbering = staticmethod(lambda m, *a: _nl.heading_numbering(win, *a))
        adjust_indents = staticmethod(lambda w: _lm.adjust_indents(w))
        set_numbering_value = staticmethod(lambda w: _lm.set_numbering_value(w))
        define_dialog = staticmethod(lambda w: _lm.define_dialog(w))
    lists = _L
def labels():
    return [getattr(p, "ListLabelString", "") for p in paras() if hasattr(p, "ListLabelString")]
def ctx_items():
    GLib.idle_add(lambda: (win.dialogs.context_menu(), False)[1])
def restart():
    fresh(); yield 0.3
    T("one\ntwo\nthree"); yield 0.3
    K("ctrl+a"); yield 0.2
    win.actions.do_numbering(); yield 0.8
    K("ctrl+End"); yield 0.3
    note("labels", labels())
    ctx_items(); yield 0.8
    ml = [l.get_text() for w in popups() for l in find_widget(w, lambda x: isinstance(x, Gtk.Label))]
    note("ctx", ml)
    check("context menu has list items", all(any(x in l for l in ml) for x in ("Restart at 1", "Continue Numbering", "Set Numbering Value", "Adjust List Indents")), ml)
    K("Escape"); yield 0.3
    lists.restart_at(M(), 1); yield 0.6
    check("Restart at 1", labels() == ["1.", "2.", "1."], labels())
    lists.continue_numbering(M()); yield 0.6
    note("after continue", labels())
    # two separate lists then continue
    fresh(); yield 0.3
    T("a\nb\n\nmid\nc\nd"); yield 0.3
    K("ctrl+Home"); K("shift+Down"); yield 0.2
    win.actions.do_numbering(); yield 0.8
    K("ctrl+End"); K("shift+Up"); K("shift+Home"); yield 0.2
    win.actions.do_numbering(); yield 0.8
    note("two lists", labels())
    lists.continue_numbering(M()); yield 0.8
    check("Continue Numbering joins previous list", labels()[-2:] == ["3.", "4."], labels())
def multilevel():
    fresh(); yield 0.3
    T("alpha\nbeta\ngamma"); yield 0.3
    K("ctrl+a"); yield 0.2
    c = find_control("Home", "Multilevel List")
    check("Multilevel List is a gallery", c is not None and callable(getattr(c, "menu", None)), c)
    box = {}
    GLib.idle_add(lambda: (box.setdefault("p", c.open_menu()), False)[1]); yield 1.0
    shot("l4_gallery")
    tips = [b.get_tooltip_text() for b in find_widget(box["p"], lambda x: isinstance(x, Gtk.Button) and x.get_tooltip_text())]
    note("tiles", tips)
    check("gallery tiles", len(tips) >= 6, tips)
    box["p"].popdown(); yield 0.3
    lists.apply_multilevel(M(), lists.MULTI[2][1]); yield 0.8
    K("ctrl+Home"); K("Down"); K("Home"); yield 0.3
    K("Tab"); yield 0.6
    check("1. 1.1. scheme with Tab demotes", labels()[:3] == ["1.", "1.1.", "2."], labels())
    shot("l4_ml")
    check("first word capitalized on Enter", para_texts()[:2] == ["Alpha", "Beta"], para_texts())
    fresh(); yield 0.3
    T("Intro\nDetail"); yield 0.5
    K("ctrl+Home"); yield 0.4; win.actions.cmd(".uno:StyleApply?Style:string=Heading 1&FamilyName:string=ParagraphStyles"); yield 0.5
    K("Down"); yield 0.4; win.actions.cmd(".uno:StyleApply?Style:string=Heading 2&FamilyName:string=ParagraphStyles"); yield 0.5
    lists.heading_numbering(M()); yield 0.8
    check("heading numbering", labels()[:2] == ["1", "1.1"], labels())
def dialogs():
    fresh(); yield 0.3
    T("x\ny"); K("ctrl+a"); win.actions.do_numbering(); yield 0.8
    GLib.idle_add(lambda: (lists.adjust_indents(win), False)[1]); yield 1.0
    check("Adjust List Indents dialog", bool(dlg("Adjust List Indents")))
    shot("l4_adjust")
    respond("Adjust List Indents"); yield 0.6
    GLib.idle_add(lambda: (lists.set_numbering_value(win), False)[1]); yield 1.0
    d = dlg("Set Numbering Value")
    check("Set Numbering Value dialog", bool(d))
    if d:
        sp = find_widget(d[0], lambda w: isinstance(w, Gtk.SpinButton))[0]
        sp.set_value(5)
        respond("Set Numbering Value"); yield 0.6
    check("Set value to 5", labels() == ["5.", "6."], labels())
    GLib.idle_add(lambda: (lists.define_dialog(win), False)[1]); yield 1.0
    check("Define New Multilevel List dialog", bool(dlg("Define New Multilevel")))
    shot("l4_define")
    respond("Define New Multilevel"); yield 0.6
    note("after define", labels())
run_scenarios(restart, multilevel, dialogs)
