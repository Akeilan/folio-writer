exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
def d():
    for seq in (["T:-"], ["T:-", "T: "], ["T:- d"], ["T:a- b"], ["K:minus"], ["T:x", "K:Return", "T:-"]):
        fresh(); yield 0.4
        for s in seq:
            if s.startswith("T:"): T(s[2:])
            else: K(s[2:])
            yield 0.4
        note(str(seq), (para_texts(), [p.NumberingIsNumber for p in paras()]))
run_scenarios(d)
