exec(open("/home/claude/folio2/tests/common.py").read())
from folio import docapi
e = win.engine; m = lambda: e.model; A = win.actions
def typ(t): return lambda: subprocess.run(["xdotool", "type", "--delay", "40", t])
def key(*k): return lambda: subprocess.run(["xdotool", "key", "--delay", "60"] + list(k))
def s0(): win.focus_document(); A.insert_text("Text with fraction ")
def eq(): win.run("equation")
def s9():
    for o in docapi.formulas(m()):
        log(docapi.formula_of(o), "size", o.Size.Width, o.Size.Height, "base", o.getEmbeddedObject().BaseFontHeight)
    shot("t137")
    win.save_to("/tmp/eqinline.docx")
def s10(): st["w2"] = app.open_path("/tmp/eqinline.docx") if hasattr(app, "open_path") else app.new_window("/tmp/eqinline.docx")
def s11():
    w2 = st["w2"]; m2 = w2.engine.model
    for o in docapi.formulas(m2):
        log("reloaded", docapi.formula_of(o), "size", o.Size.Width, o.Size.Height, "base", o.getEmbeddedObject().BaseFontHeight)
    w2.present(); shot("t137b")
    o = [o for o in docapi.formulas(m2) if "over" in docapi.formula_of(o)][0]
    w2.eqbar.edit(o); w2.eqbar.ed.load_linear("(a+b)/(c+d)^2+x_1^2"); w2.eqbar.finish()
def s12():
    w2 = st["w2"]; m2 = w2.engine.model
    for o in docapi.formulas(m2):
        log("after edit", docapi.formula_of(o), "size", o.Size.Width, o.Size.Height)
    shot("t137c")
st = {}
steps(s0, eq, typ("a/b "), key("Right"), typ(" and script "), eq, typ("x_i^2 "), key("Right"), typ(" and plain "), eq, typ("x+y"), key("Right"), typ(" end of line."), s9, s10, s11, s12, lambda: app.quit(), delay=1500)
