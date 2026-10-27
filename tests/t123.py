exec(open("/home/claude/folio2/tests/common.py").read())
from folio import docapi, pastelink
e = win.engine; m = lambda: e.model
st = {}
def s0():
    win.actions.insert_text("Alpha source sentence here.")
    e.command(".uno:SelectAll")
def s1():
    win.save_to("/tmp/pl_src.odt"); log("saved", e.path)
    e.command(".uno:SelectAll")
def s2():
    win.actions.do_copy(); log("source", bool(pastelink.SOURCE))
    st["w2"] = app.new_window()
def s3():
    w2 = st["w2"]
    w2.engine.view.grab_focus()
    log("available", pastelink.available(w2, pastelink.SOURCE.get("text")))
def s4():
    ok = pastelink.paste(st["w2"]); log("pasted", ok)
def s5():
    m2 = st["w2"].engine.model
    log("target text", repr(m2.getText().getString()[:80]), [s.Name for s in pastelink.links(m2)])
    # change source
    rd = m().createReplaceDescriptor(); rd.SearchString = "source"; rd.ReplaceString = "CHANGED"; m().replaceAll(rd)
def s6():
    win.save_to("/tmp/pl_src.odt")
    st["w2"].act_update_fields()
def s7():
    m2 = st["w2"].engine.model
    log("after update", repr(m2.getText().getString()[:80])); app.quit()
steps(s0, s1, s2, s3, s4, s5, s6, s7, delay=2500)
