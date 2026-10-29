import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
A = win.actions
def s0():
    win.unmaximize(); win.resize(1590,960); win.move(0,0)
    for i in range(3): A.insert_text("Page %d text" % i); A.cmd(".uno:InsertPagebreak")
def s1(): win.run("split")
def s2(): shot("split2"); win.run("split")
def s3():
    win.run("multiple-pages"); return
    pass
def s4(): log("rects", win.engine.page_rects()[:3]); shot("multi"); app.quit()
steps(s0, s1, s2, s3, s4, delay=2500)
