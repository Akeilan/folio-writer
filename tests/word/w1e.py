import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
def d():
    for seq in (["T:-"], ["T:-", "T: "], ["T:- d"], ["T:a- b"], ["K:minus"], ["T:x", "K:Return", "T:-"]):
        fresh(); yield 0.4
        for s in seq:
            if s.startswith("T:"): T(s[2:])
            else: K(s[2:])
            yield 0.4
        note(str(seq), (para_texts(), [is_listed(i) for i, t in enumerate(para_texts())]))
run_scenarios(d)
