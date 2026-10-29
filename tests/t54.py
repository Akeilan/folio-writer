import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
A = win.actions; m = lambda: win.engine.model
def s0(): A.insert_text("Before"); A.cmd(".uno:InsertPara"); win.dialogs._new_table(2, 2)
def s1():
    M = m(); t = M.getTextTables().getByIndex(0); text = M.getText()
    en = text.createEnumeration(); items=[]
    while en.hasMoreElements():
        el = en.nextElement(); items.append(el)
        log("el", el.getImplementationName(), el.supportsService("com.sun.star.text.TextTable"))
    p = items[0]
    try: log("p start", repr(p.getString())); c = text.createTextCursorByRange(p.getEnd()); log("cursor ok")
    except Exception as e: log("err", e)
    try:
        para = M.createInstance("com.sun.star.text.Paragraph"); text.insertTextContentBefore(para, t); log("inserted before")
    except Exception as e: log("ins err", e)
    log(repr(text.getString()))
    app.quit()
steps(s0, s1, delay=2500)
