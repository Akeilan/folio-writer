import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
from folio import citations as C
A = win.actions; m = lambda: win.engine.model
def s0():
    win.unmaximize(); win.resize(1590,960); win.move(0,0)
    A.insert_text("Research shows this ")
def s1():
    a = C.add_source(m(), {"type":"Book","author":"Smith, John","title":"The Art of Writing","year":"2020","city":"New York","publisher":"Penguin"}, master=False)
    b = C.add_source(m(), {"type":"Journal Article","author":"Jones, Ann; Brown, Bob","title":"Word processors in practice","journal":"Journal of Tools","year":"2019","volume":"12","issue":"3","pages":"45-67"}, master=False)
    c = C.add_source(m(), {"type":"Web site","author":"Lee, Kim","title":"Typing tips","journal":"Tips Site","year":"2021","url":"https://example.com/tips"}, master=False)
    C.insert_citation(m(), a["tag"]); log("tags", a["tag"], b["tag"], c["tag"])
def s2(): A.insert_text(" and also "); 
def s3():
    tags=[s["tag"] for s in C.doc_sources(m())]; C.insert_citation(m(), tags[1]); A.insert_text(". More "); C.insert_citation(m(), tags[2]); A.insert_text(".")
def s4(): A.cmd(".uno:InsertPara"); C.insert_bibliography(m(), "References")
def s5(): log("APA", repr(m().getText().getString())); win.ribbon.select([t for t in win.ribbon.tabs if t.name=="References"][0]); shot("cite_apa")
def s6(): C.set_style(m(), "MLA")
def s7(): log("MLA", repr(m().getText().getString())); C.set_style(m(), "IEEE")
def s8(): log("IEEE", repr(m().getText().getString())); shot("cite_ieee"); C.set_style(m(), "Chicago")
def s9(): log("Chicago", repr(m().getText().getString())); app.quit()
steps(s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, delay=2000)
