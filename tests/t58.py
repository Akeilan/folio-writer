import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
from folio import citations as C, docapi
A = win.actions; m = lambda: win.engine.model; st={}
def s0():
    win.unmaximize(); win.resize(1590,960); win.move(0,0); A.insert_text("Claim one ")
    a = C.add_source(m(), {"type":"Book","author":"Smith, John","title":"The Art of Writing","year":"2020"}, master=False)  # no publisher
    b = C.add_source(m(), {"type":"Journal Article","author":"Jones, Ann","title":"On Tools","journal":"J. Tools","year":"2019"}, master=False)
    C.insert_citation(m(), a["tag"]); st["a"]=a["tag"]; st["b"]=b["tag"]
def s1(): A.insert_text(" and two "); 
def s2(): C.insert_citation(m(), st["b"])
def s3():
    vc = docapi.view_cursor(m()); vc.goLeft(1, False)
    f = C.citation_at_cursor(m()); log("at cursor", f is not None, C.citation_info(m(), f) if f else None)
    C.set_citation_options(m(), f, {"pages": "45", "suppress": ["author"]})
def s4(): A.cmd(".uno:GoToEndOfDoc"); A.cmd(".uno:InsertPara"); C.insert_bibliography(m(), "References")
def s5(): log("APA", repr(m().getText().getString())); C.set_style(m(), "MLA")
def s6(): log("MLA", repr(m().getText().getString())); C.set_style(m(), "IEEE")
def s7(): log("IEEE", repr(m().getText().getString())); C.set_style(m(), "APA"); log("saved", win.save_to("/tmp/cite2.docx"))
def s8(): st["w"] = app.new_window("/tmp/cite2.docx")
def s9(): log("reopen", repr(st["w"].engine.model.getText().getString())); shot("cite2"); app.quit()
steps(s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, delay=2000)
