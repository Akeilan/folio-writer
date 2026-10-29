import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
def s0():
    win.unmaximize(); win.resize(1590, 960); win.move(0,0)
    A = win.actions
    A.apply_style("Title"); A.insert_text("Annual Report"); A.cmd(".uno:InsertPara")
    A.apply_style("Heading 1"); A.insert_text("Introduction"); A.cmd(".uno:InsertPara")
    A.apply_style("Normal"); A.insert_text("Body text that follows the heading, long enough to show a line or two in the document.")
def s1(): win.ribbon.select([t for t in win.ribbon.tabs if t.name=="Design"][0])
def s2(): shot("design0"); win.run(("style-set", "Shaded"))
def s3(): shot("design1"); win.run(("doc-theme", "Meadow"))
def s4(): shot("design2"); win.run(("style-set", "Lines (Stylish)"))
def s5():
    shot("design3"); win.ribbon.select([t for t in win.ribbon.tabs if t.name=="Home"][0])
def s6(): shot("design4"); win.actions.do_undo()
def s7(): shot("design5"); app.quit()
steps(s0, s1, s2, s3, s4, s5, s6, s7, delay=2000)
