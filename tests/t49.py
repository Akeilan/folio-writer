exec(open("/home/claude/folio2/tests/common.py").read())
from folio import docapi, bridge
m = lambda: win.engine.model
def s0():
    M = m(); vc = docapi.view_cursor(M)
    f = M.createInstance("com.sun.star.text.textfield.Bibliography")
    log("field props", [p.Name for p in f.getPropertySetInfo().getProperties()])
    f.Fields = (bridge.prop("Identifier", "Smith, 2020"), bridge.prop("BibiliographicType", 1), bridge.prop("Author", "Smith, J."), bridge.prop("Title", "A Book"), bridge.prop("Year", "2020"))
    vc.getText().insertTextContent(vc, f, False)
    fm = M.getTextFieldMasters(); names = [n for n in fm.getElementNames() if "Bibliography" in n]; log("masters", names)
    ma = fm.getByName(names[0]); log("master props", [(p.Name) for p in ma.getPropertySetInfo().getProperties()])
    ma.BracketBefore = "("; ma.BracketAfter = ")"
    M.getTextFields().refresh()
    vc.gotoEnd(False)
    idx = M.createInstance("com.sun.star.text.Bibliography")
    log("idx props", [p.Name for p in idx.getPropertySetInfo().getProperties()])
    vc.getText().insertTextContent(vc, idx, False); idx.update()
    lf = idx.LevelFormat; log("levels", lf.getCount(), [tuple((p.Name, p.Value) for p in tok) for tok in lf.getByIndex(2)])
    log("text", repr(M.getText().getString()))
def s1(): shot("bib"); app.quit()
steps(s0, s1, delay=2500)
