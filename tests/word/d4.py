import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
def a():
    fresh(); yield 0.3
    T("Base text."); yield 0.4
    win.actions.cmd(".uno:TrackChanges"); yield 0.4
    K("End"); T(" Added by me."); yield 0.8
    check("insertion tracked", "Added by me." in text() and len(changes()) >= 1, (text(), changes()))
    win.engine.command(".uno:RejectAllTrackedChanges"); yield 1.0
    check("Reject All removes the insertion", text() == "Base text." and not changes(), (text(), changes()))
    win.engine.command(".uno:Undo"); yield 1.0
    check("one undo brings it back", "Added by me." in text() and len(changes()) >= 1, (text(), undo_titles()[:5]))
    win.actions.cmd(".uno:TrackChanges"); yield 0.3
run_scenarios(a)
