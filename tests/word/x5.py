exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
def d():
    fresh(); yield 0.3
    T("Head"); K("ctrl+alt+1"); yield 0.3
    K("alt+shift+Right"); yield 0.6
    check("demote quick", style_of(0) == "Heading 2", style_of(0))
    K("alt+shift+Left"); yield 0.6
    check("promote", style_of(0) == "Heading 1", style_of(0))
    fresh(); yield 0.3
    T("hello"); K("shift+F10"); yield 1.0
    shot("x5_sf10")
    note("popups", len(popups()))
    K("Escape")
run_scenarios(d)
