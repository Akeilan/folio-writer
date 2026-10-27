exec(open("/home/claude/folio2/tests/common.py").read())
from folio import mailings as M, mailrules as MR, docapi
A = win.actions; m = lambda: win.engine.model
def s0():
    cols, rows = M.read_csv("/tmp/rcp.csv")[:2] if isinstance(M.read_csv("/tmp/rcp.csv"), tuple) else (None, None)
    log("csv", cols, rows)
    M.set_recipients(m(), cols, rows, "/tmp/rcp.csv")
    M.set_merge_type(m(), "letters")
    A.insert_text("Dear "); M.insert_field(m(), "First Name")
    A.insert_text(", ")
    MR.insert_rule(m(), {"kind": "if", "field": "Amount", "op": "gt", "value": "100", "then": "big spender", "else": "regular"})
    A.insert_text(" #"); MR.insert_rule(m(), {"kind": "record"})
    MR.insert_rule(m(), {"kind": "skipif", "field": "City", "op": "eq", "value": "Boston"})
def s1(): M.show_record(m(), 1); log("preview", repr(m().getText().getString()))
def s2(): M.show_record(m(), None); log("plain", repr(m().getText().getString()))
def s3():
    p = M.merge(m(), "all"); d = M._load_hidden(p); log("merged", repr(d.getText().getString())); d.close(True)
    log("errors", MR.find_errors(m()))
    app.quit()
steps(s0, s1, s2, s3, delay=1500)
