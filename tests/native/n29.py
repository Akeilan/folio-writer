exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
# 2.30 (2): Web Page and Rich Text without a converter, formatted copy for other programs,
# F4 repeating formatting, Ctrl+F9 field braces, deleting whole fields, Sort Text by fields,
# Set Numbering Value, the Navigation pane's heading menu, 3-D Rotation, equation shapes,
# drawing canvas, the mail merge wizard and the menu items Word has
import os
import subprocess
from gi.repository import GLib, Gtk


def body(ed):
    return [ed.para_text_of(n) for k, n, _t in ed.body_blocks() if k == "p"]


def menu_labels_of(items):
    return [it[0] for it in items if it]


def a():
    yield 1.0
    focus(); yield 0.2
    ed = E.ed

    # ---- F4 repeats bold onto text that inherited bold
    fresh(); yield 0.2
    T("repeat"); yield 0.3
    K("ctrl+shift+Left"); K("ctrl+b"); yield 0.3
    K("End"); T(" again"); K("ctrl+shift+Left"); yield 0.3
    K("F4"); yield 0.4
    f = find("again")
    check("F4 gives the same formatting again", f is not None and f.run()["bold"], f and f.run()["bold"])

    # ---- deleting a whole field takes its codes too
    fresh(); yield 0.2
    K("alt+shift+t"); yield 0.4
    fresh(); yield 0.2
    K("alt+shift+p"); yield 0.5
    check("a deleted field doesn't come back", body(ed)[0].strip() == "1", body(ed))

    # ---- Ctrl+F9
    fresh(); yield 0.2
    K("ctrl+F9"); yield 0.3
    T("PAGE"); yield 0.3
    check("Ctrl+F9: real braces with the code typed in them", ed.codes_shown()[1] == 1 and body(ed)[0].strip() == "PAGE",
          (ed.codes_shown(), body(ed)))
    K("F9"); yield 0.5
    check("F9 makes the field", body(ed)[0] == "1" and ed.body_fields(), (body(ed), ed.body_fields()))

    # ---- Web Page / Rich Text
    fresh(); yield 0.2
    for h in ("Alpha", "Beta"):
        T(h); K("ctrl+alt+1"); K("Return"); T("Body " + h); K("Return")
    yield 0.4
    os.makedirs("/tmp/n29", exist_ok=True)
    win.save_to("/tmp/n29/x.html"); yield 0.8
    h = open("/tmp/n29/x.html").read() if os.path.exists("/tmp/n29/x.html") else ""
    check("Save as Web Page without a converter", "<h1" in h and "Body Beta" in h, h[:200])
    win.save_to("/tmp/n29/x.rtf"); yield 0.8
    r = open("/tmp/n29/x.rtf").read() if os.path.exists("/tmp/n29/x.rtf") else ""
    check("Save as Rich Text without a converter", r.startswith("{\\rtf1") and "Body Alpha" in r, r[:120])

    # ---- formatted copy for other programs
    K("ctrl+Home"); K("shift+End"); K("ctrl+b"); K("ctrl+c"); yield 0.5
    p = subprocess.Popen(["xclip", "-selection", "clipboard", "-o", "-t", "text/html"], stdout=subprocess.PIPE)
    for _i in range(50):
        if p.poll() is not None:
            break
        yield 0.1
    out = p.stdout.read().decode() if p.poll() is not None else ""
    check("copy offers HTML to other programs", "Alpha" in out and "<b>" in out, out[:200])

    # ---- Navigation pane heading menu
    from folio.panes import NavigationPane
    win.toggle_navigation_pane(); yield 0.8
    pn = win.panes.get(NavigationPane)
    pn.stack.set_visible_child_name("headings"); pn.refresh_headings(); yield 0.4
    node = pn.hstore[Gtk.TreePath(1)][1]
    nodes = ed.section_paras(node)
    ed.move_paras(nodes, pn.hstore[Gtk.TreePath(0)][1], False); E.view.after_edit(); yield 0.3
    check("a heading's section moves", body(ed)[:2] == ["Beta", "Body Beta"], body(ed))
    win.toggle_navigation_pane(); yield 0.4

    # ---- Sort Text by field 2
    fresh(); yield 0.2
    T("b\t2\na\t3\nc\t1"); yield 0.5
    K("ctrl+a"); yield 0.3
    from folio import sortdlg
    sortdlg.sort_native(win, [(2, 1, True)], False, {"sep": "\t"}); yield 0.4
    check("Sort Text by a field", body(ed)[:3] == ["c\t1", "b\t2", "a\t3"], body(ed))
    K("ctrl+a"); yield 0.2
    sortdlg.sort_native(win, [(0, 2, False)], False, {"sep": "\t"}); yield 0.4
    check("Sort Text descending", body(ed)[:3] == ["c\t1", "b\t2", "a\t3"], body(ed))

    # ---- Set Numbering Value on a selection: its first item
    fresh(); yield 0.2
    T("x\ny"); K("ctrl+a"); win.actions.do_numbering(); yield 0.5
    from folio.native import lists as NL
    NL.apply_numbering_value(win, True, False, 5); yield 0.3
    labs = ed.body_labels()
    check("Set Numbering Value: 5, 6", labs[:2] == ["5.", "6."], labs)

    # ---- objects: equation shapes, 3-D rotation, canvas
    fresh(); yield 0.2
    from folio import drawing
    kinds = [it[1] for it in drawing.SHAPE_MENU if it and it[0] != "#"]
    check("equation shapes in Shapes", all(k in kinds for k in ("math-plus", "math-equal", "math-not-equal")), kinds)
    pg = 0
    ok = ed.insert_shape(drawing.PRST["math-plus"], pg, 100, 200, 72, 72, "Plus Sign", False)
    E.view.document_changed(); E.view.objs.refresh(); yield 0.3
    check("plus sign drawn", ok and "mathPlus" in (ed.selected_drawing_xml() or ""), ok)
    from folio.native import objects as NO
    NO.set_rotation(win, "perspectiveLeft"); yield 0.3
    check("3-D Rotation preset kept", "perspectiveLeft" in (ed.selected_drawing_xml() or ""))
    shot("n29_rotation")
    ed.object_delete(); E.view.after_edit(); yield 0.2
    win.insert_canvas(); yield 0.3
    x = ed.selected_drawing_xml() or ""
    check("New Drawing Canvas", "Drawing Canvas" in x and "noFill" in x, x[:120])
    ed.object_delete(); E.view.after_edit(); yield 0.2

    # ---- mail merge wizard
    from folio import dlg_mail
    d = dlg_mail.wizard(win); yield 0.5
    check("Step-by-Step Mail Merge Wizard opens", d.get_visible() and "Step 1 of 6" in [w.get_text() for w in find_widget(d, lambda w: isinstance(w, Gtk.Label))])
    d.destroy(); yield 0.2

    # ---- menus with Word's items
    src = open(os.path.join(os.path.dirname(drawing.__file__), "ribbon_defs.py")).read()
    want = ["Diagonal Down Border", "Diagonal Up Border", "Save Selection to Bibliography Gallery",
            "Just Mine", "Save Selection to Text Box Gallery", "E-mail Messages", "Normal Word Document",
            "Step-by-Step Mail Merge Wizard", "Choose from Outlook Contacts", "Send Email Messages", "3-D Rotation"]
    check("menu items as in the original", all(w in src for w in want), [w for w in want if w not in src])
    yield 0.3
run_scenarios(a)
