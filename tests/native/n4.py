import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
from folio.native.uno_model import NativeModel
from folio import modelapi as docapi, stylemodify
def a():
    yield 1.0
    focus(); yield 0.2
    T("Body text in Normal.\nA heading"); yield 0.4
    win.run(("style", "Heading 1")); yield 0.3
    m = NativeModel(E)
    fams = m.getStyleFamilies()
    st = fams.getByName("ParagraphStyles").getByName("Standard")
    check("normal found", st.DisplayName == "Normal", st.DisplayName)
    um = m.getUndoManager(); um.enterUndoContext("Modify Style")
    st.CharHeight = 14
    st.ParaBottomMargin = 0
    um.leaveUndoContext()
    yield 0.4
    r = E.ed.style_run_values("Normal")
    check("normal size 14", r["size"] == 14.0, r["size"])
    K("ctrl+Home"); yield 0.2
    check("body follows style", E.ed.state()["size"] == 14.0, E.ed.state()["size"])
    h = fams.getByName("ParagraphStyles").getByName("Heading 1")
    check("heading based on normal", h.ParentStyle in ("Standard", "Normal"), h.ParentStyle)
    # new style from formatting
    docapi.new_style(m, "My Style", based_on="Standard", follow="Standard", family="ParagraphStyles")
    yield 0.3
    names = [s[1] for s in E.ed.style_list()]
    check("new style exists", "My Style" in names, names[:40])
    # undo of the style change
    yield 0.5
    names = []
    for _ in range(6):
        names.append(E.ed.state()["undo_name"])
        E.ed.undo()
        if E.ed.style_run_values("Normal")["size"] == 11.0:
            break
    note("undid", names)
    yield 0.3
    check("style change undone", E.ed.style_run_values("Normal")["size"] == 11.0,
          E.ed.style_run_values("Normal")["size"])
    # the real Modify Style dialog opens and closes
    def ok(resp=Gtk.ResponseType.OK):
        for w in Gtk.Window.list_toplevels():
            if isinstance(w, Gtk.Dialog) and w.get_visible():
                w.response(resp)
        return False
    GLib.timeout_add(1500, ok)
    stylemodify.modify_dialog(win, "Normal"); yield 1.0
    log("after modify dialog")
    GLib.timeout_add(1500, lambda: ok(Gtk.ResponseType.CANCEL))
    win.run("new-style"); yield 1.0
    check("alive", True)
run_scenarios(a)
