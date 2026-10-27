exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
def a():
    fresh(); yield 0.3
    t = M().getText(); c = t.createTextCursor()
    for h in ("Alpha", "Beta", "Gamma"):
        t.insertString(c, h, False); c.ParaStyleName = "Heading 1"; t.insertControlCharacter(c, 0, False)
        c.ParaStyleName = "Standard"; t.insertString(c, "Body " + h, False); t.insertControlCharacter(c, 0, False)
    yield 0.5
    hs = docapi.headings(M())
    docapi.move_section(M(), hs[2][2], hs[0][2], False); yield 0.5
    note("after", para_texts())
run_scenarios(a)
