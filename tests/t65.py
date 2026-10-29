import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
from folio import bridge, docapi
A = win.actions; m = lambda: win.engine.model
def s0(): win.unmaximize(); win.resize(1590,960); win.move(0,0); A.insert_text("This is is a test.  i went to a apple store,and bought alot of things. He should of known.")
def s1():
    loc = docapi.locale("en", "US")
    lsm = bridge.create("com.sun.star.linguistic2.LinguServiceManager")
    log("configured", lsm.getConfiguredServices("com.sun.star.linguistic2.Proofreader", loc))
    lsm.setConfiguredServices("com.sun.star.linguistic2.Proofreader", loc, ("org.openoffice.comp.pyuno.Lightproof.lightproof_en",))
    A.cmd(".uno:GoToEndOfDoc"); A.insert_text(" ")
def s2():
    try:
        M = m(); para = M.getText().createEnumeration().nextElement(); text = para.getString()
        loc = docapi.locale("en", "US")
        lsm = bridge.create("com.sun.star.linguistic2.LinguServiceManager")
        log("grammar services", lsm.getAvailableServices("com.sun.star.linguistic2.Proofreader", loc))
        pr = bridge.create("org.openoffice.comp.pyuno.Lightproof.lightproof_en")
        log("pr", pr)
        res = pr.doProofreading("1", text, loc, 0, len(text), ())
        log("errors", [(e.nErrorStart, e.nErrorLength, e.aShortComment, list(e.aSuggestions)[:2]) for e in res.aErrors])
    except Exception as e:
        log("iter err", e)
    shot("grammar"); app.quit()
steps(s0, s1, s2, delay=3000)
