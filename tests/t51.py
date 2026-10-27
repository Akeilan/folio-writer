exec(open("/home/claude/folio2/tests/common.py").read())
from folio import bridge, docapi
import uno, traceback
m = lambda: win.engine.model
def s0():
    M=m(); idx = M.createInstance("com.sun.star.text.Bibliography"); vc=docapi.view_cursor(M)
    vc.getText().insertTextContent(vc, idx, False)
    lf = idx.LevelFormat
    toks = ((bridge.prop("TokenType","TokenText"), bridge.prop("CharacterStyleName",""), bridge.prop("Text","X: ")),
            (bridge.prop("TokenType","TokenBibliographyDataField"), bridge.prop("CharacterStyleName",""), bridge.prop("BibliographyDataField",4)))
    try:
        lf.replaceByIndex(2, toks); log("plain ok")
    except Exception as e:
        log("plain err", type(e), e.typeName if hasattr(e,'typeName') else '', getattr(e,'Message',''))
    try:
        uno.invoke(lf, "replaceByIndex", (2, uno.Any("[][]com.sun.star.beans.PropertyValue", toks))); log("any ok")
    except Exception as e:
        log("any err", type(e), getattr(e,'Message',''))
    idx.LevelFormat = lf
    log("level2", [tuple((p.Name,p.Value) for p in t) for t in idx.LevelFormat.getByIndex(2)])
    app.quit()
steps(s0, delay=2500)
