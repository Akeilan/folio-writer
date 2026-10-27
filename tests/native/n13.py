exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
import json
def a():
    yield 1.0
    focus(); yield 0.2
    ed = E.ed
    ed.type_text("The quick brown fox jumps over the lazy dog.\nSecond paragraph.")
    E.view.after_edit(); yield 0.3
    E.command(".uno:TrackChanges"); yield 0.2
    ed.move_caret("doc_start", False)
    for _ in range(4):
        ed.move_caret("right", False)
    for _ in range(6):
        ed.move_caret("right", True)
    E.view.after_move()
    K("BackSpace"); yield 0.4
    # bold "brown" (now at 4..9)
    ed.move_caret("doc_start", False)
    for _ in range(4):
        ed.move_caret("right", False)
    for _ in range(5):
        ed.move_caret("right", True)
    E.view.after_move()
    K("ctrl+b"); yield 0.4
    win.set_markup_display("All Markup"); yield 0.5
    win.set_balloons(True); yield 0.8
    check("balloons on", E.get(".uno:ShowChangesInMargin") == "true")
    v = json.loads(E.view.get_command_values(".uno:ViewAnnotations"))
    labels = [r["text"] for r in v.get("revisions", [])]
    check("deleted balloon", any(l.startswith("Deleted: quick") for l in labels), str(labels))
    check("format balloon", any(l.startswith("Formatted: Bold") for l in labels), str(labels))
    ed.move_caret("doc_start", False); ed.move_caret("end", True)
    check("deletion not inline", "quick" not in ed.selected_text(), ed.selected_text())
    check("cards", len(win.comments.cards) >= 2, str([(r["text"], r["anchorPos"]) for r in v.get("revisions", [])]))
    shot("n13_balloons")
    win.set_balloons(False); yield 0.6
    ed.move_caret("doc_start", False); ed.move_caret("end", True)
    check("inline again", "quick" in ed.selected_text(), ed.selected_text())
run_scenarios(a)
