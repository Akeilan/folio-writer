import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
from folio import docapi, drawing
A = win.actions
m = lambda: win.engine.model
def s0(): A.insert_text("Text before. ")
def s1(): docapi.insert_picture(m(), "/tmp/pic.png")
def s2():
    c = m().getCurrentController(); sel = c.getSelection()
    log("sel1", sel.getImplementationName(), win.engine.selection_type())
    g = m().getGraphicObjects().getByIndex(0)
    log("select returns", c.select(g), "immediately", c.getSelection().getImplementationName(), "anchor", g.AnchorType.value, "graphic", g.Graphic is not None)
def s3():
    sel = m().getCurrentController().getSelection(); log("sel2", sel.getImplementationName(), win.engine.selection_type())
    r = win.engine.page_rects()[0]
    win.engine.click_at(r[0] + 1440 + 1500, r[1] + 1440 + 1500)
def s4():
    sel = m().getCurrentController().getSelection(); log("sel3 after click", sel.getImplementationName(), win.engine.selection_type())
    cs = m().getCurrentSelection(); log("model cur sel", cs.getImplementationName() if cs else None)
    vc = m().getCurrentController().getViewCursor(); log("vc text", vc.getText().getImplementationName(), repr(vc.getString()))
    try:
        log("sel count", sel.getCount(), sel.getByIndex(0).getImplementationName(), repr(sel.getByIndex(0).getString()))
    except Exception as e: log("e", e)
    dp = m().getDrawPage()
    for i in range(dp.getCount()):
        sh = dp.getByIndex(i); p = sh.getPosition(); z = sh.getSize()
        log("shape", sh.getImplementationName(), p.X, p.Y, z.Width, z.Height)
    log("page rect twips", win.engine.page_rects()[:1])
    ctrls = m().getControllers(); n=0
    while ctrls.hasMoreElements(): ctrls.nextElement(); n+=1
    log("controllers", n); app.quit()
steps(s0, s1, s2, s3, s4, delay=2000)
