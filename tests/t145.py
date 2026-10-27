exec(open("/home/claude/folio2/tests/common.py").read())
from folio import docapi
from folio.eqn import model as M
e = win.engine; m = lambda: e.model; A = win.actions
ed = lambda: win.eqbar.ed
def op(label):
    for g in ed().structure_menu():
        for l, cb, _ in g:
            if l == label:
                cb(); return True
    log("MISSING", label, [[x[0] for x in g] for g in ed().structure_menu()])
def put(path):
    ed().caret = (ed()._follow(path), 0)
def s0():
    e.view.set_zoom(2.0)
    A.insert_text("Eq ")
    win.eqbar.new_equation("a/b+√(n&x)+y_1^2+■(1&2@3&4)"); win.eqbar.finish()
    A.insert_text(" end.")
def s1():
    win.eqbar.edit(docapi.formulas(m())[0])
def s2():
    r = ed().root
    log("items", [type(i).__name__ for i in r.items])
    fi = next(i for i, n in enumerate(r.items) if type(n).__name__ == "Frac")
    put([(fi, 0)]); op("Change to Skewed Fraction")
    log("skew", M.to_linear(ed().root))
    ri = next(i for i, n in enumerate(ed().root.items) if type(n).__name__ == "Root")
    put([(ri, 1)]); op("Hide Degree")
    log("root", M.to_linear(ed().root))
    si = next(i for i, n in enumerate(ed().root.items) if type(n).__name__ == "Script")
    put([(si, 0)]); op("Change to Prescript")
    log("pre", M.to_linear(ed().root))
    mi = next(i for i, n in enumerate(ed().root.items) if type(n).__name__ == "Matrix")
    put([(mi, 0)]); op("Insert Column After"); op("Insert Row Below")
    log("mat", M.to_linear(ed().root))
    put([(mi, 0)]); op("Delete Row")
    log("mat2", M.to_linear(ed().root))
    ed().changed()
def s3():
    win.eqbar.finish()
def s4():
    o = docapi.formulas(m())[0]
    log("markup", o.Model.Formula)
    shot("t145a")
def s5():
    win.eqbar.edit(docapi.formulas(m())[0])
def s6():
    log("reload", M.to_linear(ed().root)); shot("t145b"); win.eqbar.finish(); app.quit()
steps(s0, s1, s2, s3, s4, s5, s6, delay=2000)
