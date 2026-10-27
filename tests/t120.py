exec(open("/home/claude/folio2/tests/common.py").read())
from folio import docapi, objecttools
e = win.engine; m = lambda: e.model; ed = win.eqbar.ed
def typ(s): return lambda: subprocess.run(["xdotool", "type", "--delay", "40", s])
def key(*k): return lambda: subprocess.run(["xdotool", "key", "--delay", "80"] + list(k))
def st(n): return lambda: log(n, "active", ed.active, "mode", ed.mode, "lin", repr(win.eqbar.entry.get_text()), "caret", ed.caret[1], len(ed.caret[0].items))
def s0():
    win.actions.insert_text("Intro text."); e.command(".uno:InsertPara")
    win.eqbar.new_equation("a/b+c")
def gal(): win.eqbar.insert("√(⬚)")
def click_eq():
    win.eqbar.finish()
    e.command(".uno:GoToStartOfDoc")
def click2():
    # click the middle of the numerator via real mouse
    o = docapi.formulas(m())[0]
    docapi.select_object(m(), o)
def sel2(): win.eqbar._selection_changed()
steps(s0, st("new"), key("Home"), st("home"), key("Right"), st("in-num"), key("Down"), st("den"), typ("x"), st("den x"),
      key("End"), typ("+"), lambda: gal(), typ("2"), st("sqrt"), lambda: shot("t120a"),
      lambda: win.eqbar.convert("linear"), st("linear"), lambda: shot("t120b"), typ(" z"),
      lambda: win.eqbar.convert("professional"), st("pro"),
      key("End"), typ("#(1)"), click_eq, lambda: log("para", repr(docapi.formulas(m())[0].getAnchor().getText().getString()[:80]), docapi.formula_of(docapi.formulas(m())[0])),
      lambda: shot("t120c"), click2, sel2, st("reopen"), lambda: shot("t120d"),
      key("BackSpace"), st("bs1"), key("BackSpace"), st("bs2"), key("ctrl+z"), st("undo"), key("Escape"),
      lambda: log("final", [docapi.formula_of(o) for o in docapi.formulas(m())]),
      lambda: app.quit(), delay=900)
