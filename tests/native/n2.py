exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
import traceback
def a():
    yield 1.0
    focus(); yield 0.2
    T("Alpha beta gamma delta.\nSecond paragraph here."); yield 0.4
    K("ctrl+a"); yield 0.2
    acts = [".uno:Italic", ".uno:Underline", ".uno:Strikeout", ".uno:SuperScript", ".uno:SubScript",
            ".uno:CenterPara", ".uno:RightPara", ".uno:JustifyPara", ".uno:LeftPara",
            "grow-font", "shrink-font", "all-caps", "small-caps", "double-underline", "highlight",
            "font-color", "indent", "outdent", "hanging-indent", "unhang", "spacing-15", "spacing-1",
            "space-before-toggle", "clear-char-format", "clear-all-formatting", "bullets",
            "insert-table-dialog", "spelling", "find-pane", "zoom-in", "zoom-out",
            ("style", "Title"), ("style", "Heading 2"), ("style", "Normal"), "undo", "redo-repeat",
            "copy", "paste", "format-painter", "change-case-cycle", "insert-page-break", "show-marks"]
    for act in acts:
        try:
            win.run(act)
        except Exception:
            check("action %s" % (act,), False, traceback.format_exc().splitlines()[-1])
        yield 0.15
    win.actions.font_name("Arial"); yield 0.2
    win.actions.font_size(14); yield 0.2
    s = E.ed.state()
    check("font set", s["font"] == "Arial" and s["size"] == 14.0, (s["font"], s["size"]))
    # mouse: click into the first word, double-click selects it
    v = E.view
    x, y = v.to_widget(0, 80, 80)
    X("mousemove", int(x) + 0, int(y) + 0)
    shot("n2"); yield 0.3
    check("alive", True)
run_scenarios(a)
