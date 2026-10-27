exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
exec(open("/home/claude/folio2/tests/word/w2.py").read().split("def clicks():")[0].split('exec(open("/home/claude/folio2/tests/word/wc.py").read())')[1])
def nums():
    return [bool(p.NumberingIsNumber) for p in paras()]
def r1():
    yield from setup_text()
    note("bullets after setup", nums())
    yield from at_word("charlie")
    click(*AT["xy"]); yield 0.4
    X("click", "--repeat", 3, "--delay", 60, 1); yield 0.8
    note("triple fast", repr(sel()))
    click(*AT["xy"]); yield 0.4
    yield from at_word("bravo", frac=0.0); a = AT["xy"]
    yield from at_word("echo", frac=1.0); b = AT["xy"]
    click(*a); yield 0.5
    note("caret before shift-click", repr(vc().getStart().getText().createTextCursorByRange(vc().getStart()).getString()))
    X("mousemove", *b); X("keydown", "shift"); time.sleep(0.1); X("click", 1); time.sleep(0.1); X("keyup", "shift"); yield 0.6
    note("shift+click", repr(sel()))
    note("bullets now", nums())
    X("mousemove", *a); X("keydown", "ctrl"); time.sleep(0.1); X("click", 1); time.sleep(0.1); X("keyup", "ctrl"); yield 0.6
    note("ctrl+click", repr(sel()))
    note("bullets now2", nums())
    shot("w2b_after")
def r2():
    yield from setup_text()
    yield from at_word("charlie")
    click(*AT["xy"], n=2); yield 0.8
    X("click", 3); yield 1.5
    shot("w2b_ctx")
    note("popups", [type(w).__name__ for w in popups()])
    note("labels", [l for l in menu_labels() if l])
    K("Escape"); yield 0.5
    click(*AT["xy"]); yield 0.4
    X("click", 3); yield 1.5
    shot("w2b_ctx_nosel")
    note("labels nosel", [l for l in menu_labels() if l])
    K("Escape"); yield 0.5
def r3():
    yield from setup_text()
    docapi.controller(M()).select(find("bravo charlie delta")); yield 0.6
    yield from at_word("charlie", frac=0.5); s = AT["xy"]
    yield from at_word("words", frac=1.0); d = AT["xy"]
    docapi.controller(M()).select(find("bravo charlie delta")); yield 0.6
    note("sel before drag", repr(sel()))
    X("mousemove", s[0], s[1]); time.sleep(0.2); X("mousedown", 1); time.sleep(0.3)
    for i in range(1, 16):
        X("mousemove", int(s[0] + (d[0] - s[0]) * i / 15), int(s[1] + (d[1] - s[1]) * i / 15)); time.sleep(0.08)
    time.sleep(0.3); X("mouseup", 1); yield 1.2
    note("after dnd", para_texts())
    shot("w2b_dnd")
run_scenarios(r1, r2, r3)
