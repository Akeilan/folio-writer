exec(open("/home/claude/folio2/tests/common.py").read())
e = win.engine
from folio import charts
st = {}
def s0(): win.present(); win.actions.insert_text("Chart below. ")
def s1(): st["o"] = charts.insert_chart(e.model, 0); 
def s2(): ds = charts.DataSheet(win, st["o"]); st["ds"] = ds
def s3():
    ds = st["ds"]; ds.data["values"][0][0] = 9.0; ds.push()
    charts.set_type(st["o"], 3)
def s4(): shot("t13"); st["ds"].destroy()
def s5():
    e.save_as("/tmp/chart.docx", "docx", keep=False)
    import zipfile; z = zipfile.ZipFile("/tmp/chart.docx"); log("chart parts", [n for n in z.namelist() if "chart" in n])
    app.quit()
steps(s0, s1, s2, s3, s4, s5, delay=1800)
