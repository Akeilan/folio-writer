exec(open("/home/claude/folio2/tests/common.py").read())
from folio import grammar, docapi
e = win.engine; m = lambda: e.model; A = win.actions
def s0():
    A.insert_text("Base xx ")
    win.eqbar.new_equation("x+y"); win.eqbar.finish()
    A.insert_text(" xx end.")
def s1x():
    it = m().getFlatParagraphIterator(2, True)   # PROOFREADING
    p = it.getFirstPara()
    while p is not None:
        t = p.getText(); log("flat", repr(t))
        pr = grammar._proofreader(); loc = docapi.locale("en", "US")
        r = pr.doProofreading("1", t, loc, 0, len(t), ())
        log([(x.nErrorStart, x.nErrorLength, x.aRuleIdentifier, x.aShortComment) for x in r.aErrors])
        p = it.getNextPara()
    app.quit()
steps(s0, lambda: None, lambda: app.quit(), delay=3000)
