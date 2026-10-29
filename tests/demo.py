import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
e = win.engine
A = win.actions
def s1():
    A.apply_style("Title"); A.insert_text("Quarterly Report"); e.command(".uno:InsertPara")
def s2():
    A.apply_style("Heading 1"); A.insert_text("Summary"); e.command(".uno:InsertPara")
def s3():
    A.insert_text("Revenue grew steadily this quarter. The growth model below fits the data well: ")
def s4():
    win.eqbar.new_equation("R(t)=R_0 e^(kt)")
def s5():
    win.eqbar.finish(); e.command(".uno:InsertPara")
def s6():
    A.apply_style("Heading 1"); A.insert_text("Details"); e.command(".uno:InsertPara")
def s7():
    e.command(".uno:InsertTable", {"Columns": ("long", 3), "Rows": ("long", 3)})
def s8():
    for t in ["Region", "Q1", "Q2"]:
        A.insert_text(t); e.command(".uno:GoToNextCell") if False else e.command(".uno:JumpToNextCell")
def s9():
    win.dialogs.table_style("blue")
def s10():
    shot("demo")
    app.quit()
steps(s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, delay=1300)
