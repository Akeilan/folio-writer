exec(open("/home/claude/folio2/tests/common.py").read())
from folio import docapi
e = win.engine; m = lambda: e.model
def s0():
    o = docapi.insert_formula(m(), "{a over b} + x^2 = sum from {i=1} to n i", display=True)
    emb = o.getEmbeddedObject()
    names = sorted(p.Name for p in emb.getPropertySetInfo().getProperties())
    log([n for n in names if "Font" in n or "Margin" in n or "Spac" in n or "Dist" in n][:80])
    log("vars font", emb.FontNameVariables, emb.FontNameNumbers, emb.FontNameFunctions, emb.FontNameText, emb.BaseFontHeight)
    app.quit()
steps(s0, delay=2000)
