import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
e = win.engine
def s0(): win.present(); win.actions.insert_text("This sentence gets a comment. And tracked edits follow."); e.command(".uno:SelectWord")
def s1(): e.command(".uno:InsertAnnotation", {"Text": "Check this wording.", "Author": "Ron"})
def s2(): e.command(".uno:TrackChanges"); e.command(".uno:GoToEndOfDoc")
def s3(): win.actions.insert_text(" Inserted while tracking.")
def s4(): e.command(".uno:GoToStartOfDoc"); e.command(".uno:DelToEndOfWord")
def s5(): shot("t14"); log("comments", len(__import__("folio.docapi", fromlist=["x"]).comments(e.model))); app.quit()
steps(s0, s1, s2, s3, s4, s5, delay=1500)
