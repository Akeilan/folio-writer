exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
import zipfile, json
def a():
    yield 1.0
    focus(); yield 0.2
    ed = E.ed
    ed.type_text("The quick fox jumps.\nSecond paragraph here.")
    E.view.after_edit(); yield 0.3
    # Ctrl+Shift+E turns tracking on
    K("ctrl+shift+e"); yield 0.4
    check("tracking on", E.get(".uno:TrackChanges") == "true", E.get(".uno:TrackChanges"))
    ed.move_caret("doc_start", False)
    for _ in range(10):
        ed.move_caret("right", False)
    E.view.after_move()
    for c in "brown ":
        K(c if c != " " else "space")
    yield 0.3
    # delete "quick "
    ed.move_caret("doc_start", False)
    for _ in range(4):
        ed.move_caret("right", False)
    for _ in range(6):
        ed.move_caret("right", True)
    E.view.after_move()
    K("BackSpace"); yield 0.4
    check("simple markup hides deletion", ed.selected_text() == "" and
          "quick" not in E.selection() )
    ch = ed.changes()
    check("two changes", len(ch) == 2, str(ch))
    # comment on "Second"
    ed.move_caret("doc_end", False)
    ed.move_caret("home", False)
    E.view.after_move()
    E.command(".uno:InsertAnnotation", {"Text": "Is this right?", "Author": "Tester"}); yield 0.8
    v = json.loads(E.view.get_command_values(".uno:ViewAnnotations"))
    cs = v["comments"]
    check("comment reported", len(cs) == 1 and cs[0]["text"] == "Is this right?", str(cs))
    check("comment anchored", bool(cs and cs[0]["anchorPos"] and cs[0]["textRange"]))
    check("balloon shown", len(win.comments.cards) == 1, str(win.comments.cards))
    win.comments.reply(cs[0]["id"]) if False else E.command(".uno:ReplyComment", {"Id": cs[0]["id"], "Text": "Yes", "Author": "Ann"})
    yield 0.5
    check("reply", len(win.comments.comments) == 2)
    win.set_markup_display("All Markup"); yield 0.6
    shot("n11_all")
    check("all markup", ed.markup() == "all")
    win.set_markup_display("Simple Markup"); yield 0.6
    shot("n11_simple")
    win.save_to("/tmp/n11.docx"); yield 0.8
    z = zipfile.ZipFile("/tmp/n11.docx")
    d = z.read("word/document.xml").decode()
    check("ins saved", "<w:ins " in d and "<w:del " in d)
    check("comment saved", "word/comments.xml" in z.namelist() and "commentRangeStart" in d)
    check("settings tracked", "trackRevisions" in z.read("word/settings.xml").decode())
    # next change, accept all
    ed.move_caret("doc_start", False)
    E.command(".uno:NextTrackedChange"); yield 0.3
    check("next change selects", ed.has_selection())
    E.command(".uno:AcceptAllTrackedChanges"); yield 0.5
    check("accepted", ed.changes() == [])
    ed.move_caret("doc_start", False); ed.move_caret("end", True)
    check("final text", ed.selected_text() == "The brown fox jumps.", ed.selected_text())
    E.command(".uno:DeleteAllNotes"); yield 0.5
    check("comments gone", len(win.comments.comments) == 0)
    win.stop_tracking(); yield 0.3
    check("tracking off", E.get(".uno:TrackChanges") == "false")
run_scenarios(a)
