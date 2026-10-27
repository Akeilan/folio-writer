exec(open("/home/claude/folio2/tests/common.py").read())
e = win.engine
A = win.actions
st = {}
def s0(): A.apply_style("Heading 1"); A.insert_text("Roundtrip"); e.command(".uno:InsertPara")
def s1(): A.insert_text("Body with "); e.command(".uno:Bold"); A.insert_text("bold"); e.command(".uno:Bold")
def s2(): win.eqbar.new_equation("E=mc^2")
def s3(): win.eqbar.finish(); log("modified before save", e.modified)
def s4():
    ok = win.save_to("/tmp/rt_test.docx"); log("saved", ok, "title", win.get_title(), "modified", e.modified)
def s5():
    w2 = app.new_window("/tmp/rt_test.docx"); st["w2"] = w2
def s6():
    w2 = st["w2"]; log("windows", len(app.windows), "w2 title", w2.get_title())
def s7():
    w2 = st["w2"]; m = w2.engine.model
    from folio import docapi
    log("w2 text", repr(m.getText().getString()[:60]), "formulas", [docapi.formula_of(o) for o in docapi.formulas(m)], "headings", [h[1] for h in docapi.headings(m)])
    log("w1 still", repr(e.model.getText().getString()[:30]))
    shot("t16"); app.quit()
steps(s0, s1, s2, s3, s4, s5, s6, s7, delay=2000)
