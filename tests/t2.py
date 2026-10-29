import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
e = win.engine
import time
t0=[0]
def onres(v, r):
    log("RESULT", round(time.time()-t0[0],3), r[:150])
e.view.connect("command-result", onres)
def s1():
    t0[0]=time.time()
    import json
    e.view.post_command(".uno:InsertText", json.dumps({"Text":{"type":"string","value":""}}), True)
    e.view.post_command(".uno:ControlCodes", "{}", True)
    e.view.post_command(".uno:ControlCodes", "{}", True)
    e.view.post_command(".uno:LanguageStatus", "{}", True)
    log("modified", e.modified)
def s2():
    log('modified after', e.modified)
    app.quit()
steps(s1, s2, delay=2500)
