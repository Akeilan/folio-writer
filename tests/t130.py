exec(open("/home/claude/folio2/tests/common.py").read())
from folio import docapi, editfeatures as EF
e = win.engine; m = lambda: e.model; A = win.actions
def scr(x, y):
    ok, ox, oy = e.view.get_window().get_origin(); return int(ox + x), int(oy + y)
def s0():
    for h, body in (("Chapter One", "First chapter text. " * 6), ("Chapter Two", "Second chapter text. " * 6)):
        A.apply_style("Heading 1"); A.insert_text(h); e.command(".uno:InsertPara")
        A.apply_style("Normal"); A.insert_text(body); e.command(".uno:InsertPara")
def s1():
    win.folds.refresh(); log("marks", [(round(x), round(y)) for _p, _l, x, y, _h in win.folds.marks])
    par = win.folds.marks[0][0]; win.folds.toggle(par, 1)
def s2():
    shot("t130a"); log("collapsed", len(win.folds.collapsed), "modified", e.modified)
    e.save_as("/tmp/fold.docx", "docx", keep=False)
    import zipfile; x = zipfile.ZipFile("/tmp/fold.docx").read("word/document.xml").decode()
    log("vanish in saved docx", x.count("<w:vanish"), x.count('<w:vanish w:val="false"'))
    win.folds.expand_all()
def s3():
    # click and type: double-click well below the text
    vc = docapi.view_cursor(m()); vc.gotoEnd(False)
    p = EF._to_twips(win, vc.getPosition()); log("end twips", p)
    x, y = e.twips_to_px(p[0] + 5000, p[1] + 3000); sx, sy = scr(x, y)
    subprocess.run(["xdotool", "mousemove", str(sx), str(sy), "click", "1"])
    subprocess.run(["xdotool", "mousemove", str(sx), str(sy), "click", "--repeat", "2", "--delay", "80", "1"])
def s4():
    A.insert_text("Typed here")
    vc = docapi.read_cursor(m()); log("c&t para adjust", vc.ParaAdjust, "paras", len(m().getText().getString().split("\n")))
    shot("t130b")
def s5():
    # spike
    vc = docapi.view_cursor(m()); vc.gotoStart(False); vc.gotoEndOfParagraph(True) if hasattr(vc,"gotoEndOfParagraph") else vc.goRight(11, True)
def s6(): win.run("spike")
def s7():
    vc = docapi.view_cursor(m()); vc.gotoEnd(False); vc.goLeft(10, True); win.run("spike")
def s8():
    vc = docapi.view_cursor(m()); vc.gotoEnd(False); e.command(".uno:InsertPara"); win.run("spike-paste")
def s9():
    log("text tail", repr(m().getText().getString()[-60:]), "spike left", len(getattr(app, "spike", [])))
    e.save_as("/tmp/resume.odt", "odt", keep=True)
def s10():
    en = m().getText().createEnumeration(); ps = [en.nextElement() for _ in range(5)]
    docapi.view_cursor(m()).gotoRange(ps[4].getStart(), False)
    log("para idx", EF._para_index(m())[0], "path", e.path); EF.remember_position(win); log("resume rec", app.settings.get("resume", {}).get("/tmp/resume.odt"))
    EF.offer_resume(win)
def s11(): shot("t130c"); app.quit()
steps(s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, delay=1500)
