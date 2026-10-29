import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
from folio import insertextras as IX
m = lambda: win.engine.model
def s0():
    m().getDocumentProperties().Title = "T1"; m().getDocumentProperties().Author = "Ron"
    for k in ("Title","Author","Keywords","Company"):
        try: IX.insert_doc_property(m(), k); win.actions.insert_text("|")
        except Exception as e: log(k, e)
def s1(): log(repr(m().getText().getString())); app.quit()
steps(s0, s1, delay=1500)
