exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
from folio import covers
def a():
    fresh(); yield 0.3
    M().getText().setString("Body text"); yield 0.5
    covers.insert_cover(win, "Sideline"); yield 1.0
    note("paras", para_texts())
    bms = M().getBookmarks()
    note("bm", (bms.hasByName("_CoverPage"), bms.getElementNames()))
    if bms.hasByName("_CoverPage"):
        note("bm text", repr(bms.getByName("_CoverPage").getAnchor().getString()))
    covers.remove_cover(M()); yield 0.8
    note("after remove", para_texts())
run_scenarios(a)
