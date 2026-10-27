exec(open("/home/claude/folio2/tests/common.py").read())
import subprocess
e = win.engine
def key(k):
    subprocess.run(["xdotool", "key", "--clearmodifiers", k], env=dict(os.environ, DISPLAY=":99"))
def typ(t):
    subprocess.run(["xdotool", "type", t], env=dict(os.environ, DISPLAY=":99"))
checks = []
def s0():
    win.present(); win.focus_document()
def s1(): typ("Hello world"); key("ctrl+a")
def s2(): key("ctrl+b")
def c2(): log("ctrl+b bold:", e.get(".uno:Bold"))
def s3(): key("ctrl+e")
def c3(): log("ctrl+e center:", e.get(".uno:CenterPara"))
def s4(): key("ctrl+bracketright")
def c4(): log("ctrl+] size:", e.get(".uno:FontHeight"))
def s5(): key("ctrl+shift+greater")
def c5(): log("ctrl+shift+> size:", e.get(".uno:FontHeight"))
def s6(): key("ctrl+alt+1")
def c6(): log("ctrl+alt+1 style:", e.get(".uno:StyleApply"))
def s7(): key("End"); key("Return"); key("alt+equal")
def c7(): log("alt+= eqbar open:", win.eqbar.ed.active, "focus in entry:", win.eqbar.entry.has_focus())
def s8(): typ("a^2+b^2"); key("Return")
def c8():
    from folio import docapi
    log("undo stack:", e.model.getUndoManager().getAllUndoActionTitles()[:6])
    log("formulas:", [docapi.formula_of(o) for o in docapi.formulas(e.model)], "bar:", win.eqbar.ed.active)
def s9():
    e.command(".uno:Undo", {"Repair": ("boolean", "true")})
    e.command(".uno:Undo", {"Repair": ("boolean", "true")})
def c9(): log("stack after", e.model.getUndoManager().getAllUndoActionTitles()[:3]); log("after undo formulas:", len(__import__("folio.docapi", fromlist=["x"]).formulas(e.model)))
def s10(): key("alt"); 
def c10(): log("alt tap keytips:", win.keytips.active)
def s11(): key("n")
def c11(): log("then N tab:", win.ribbon.current.name if win.ribbon.current else None)
def s12(): key("Escape"); key("Escape")
def c12(): log("esc keytips:", win.keytips.active); shot("t10"); app.quit()
steps(s0, s1, s2, c2, s3, c3, s4, c4, s5, c5, s6, c6, s7, c7, s8, c8, s9, c9, s10, c10, s11, c11, s12, c12, delay=900)
