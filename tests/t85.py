exec(open("/home/claude/folio2/tests/common.py").read())
from folio import insertextras as IX
m = lambda: win.engine.model
def s0():
    m().getDocumentProperties().Title = "T1"; m().getDocumentProperties().Author = "Ron"
    for k in ("Title","Author","Keywords","Company"):
        try: IX.insert_doc_property(m(), k); win.actions.insert_text("|")
        except Exception as e: log(k, e)
def s1(): log(repr(m().getText().getString())); app.quit()
steps(s0, s1, delay=1500)
