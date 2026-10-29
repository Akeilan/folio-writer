import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
from folio import docapi
m = lambda: win.engine.model
def s0(): win.actions.insert_text("Date: "); win.actions.cmd(".uno:InsertDateField"); win.actions.insert_text(" and page ")
def s1(): win.actions.cmd(".uno:InsertPageNumberField"); win.actions.cmd(".uno:GoToStartOfDoc")
def s2(): win.actions.run(("model", "goto_field", True))
def s3(): log("sel1", repr(docapi.view_cursor(m()).getString())); win.actions.run(("model", "goto_field", True))
def s4(): log("sel2", repr(docapi.view_cursor(m()).getString())); win.actions.run(("model", "goto_field", False))
def s5(): log("sel3", repr(docapi.view_cursor(m()).getString())); win.actions.run(("model", "unlink_fields"))
def s6(): log("fields left", len(docapi._fields_in_order(m())), repr(m().getText().getString())); app.quit()
steps(s0, s1, s2, s3, s4, s5, s6, delay=1200)
