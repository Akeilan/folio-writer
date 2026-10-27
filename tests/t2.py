exec(open("/home/claude/folio2/tests/common.py").read())
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
