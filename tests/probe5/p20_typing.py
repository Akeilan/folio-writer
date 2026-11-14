import os as _o; TESTS = _o.environ["FOLIO_WRITER_TESTS"]; exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read()); exec(open("/tmp/p5/probes/ph.py").read())
CASES = [
    ('"Hello," she said.', '“Hello,” she said.'),
    ("'Hello,' she said.", '‘Hello,’ she said.'),
    ("It's the dog's bone.", 'It’s the dog’s bone.'),
    ("\"'Twas late,\" he said.", '“’Twas late,” he said.'),
    ("\"I said 'no' twice.\"", '“I said ‘no’ twice.”'),
    ("Rock 'n' roll in the '90s.", 'Rock ’n’ roll in the ’90s.'),
    ("He paused--then ran.", 'He paused—then ran.'),
    ("Wait... what?", 'Wait… what?'),
    ("(\"Quoted in brackets.\")", '(“Quoted in brackets.”)'),
    ("She said--\"Go!\"", 'She said—“Go!”'),
    ("the end. new sentence starts", 'The end. New sentence starts'),
    ("teh adn recieve", 'The and receive'),
    ("1st 2nd 3rd 1/2 (c) (tm)", None),
    ("i think i am", 'I think I am'),
    ("e.g. this and i.e. that. etc. more", None),
    ("Mr. smith and Dr. jones met at 5 p.m. yesterday", None),
    ("* * *", '* * *'),
    ("5'10\" tall", None),
    ("www.example.com and me@example.com ", None),
]
def a():
    yield 0.5
    focus()
    for src, want in CASES:
        fresh(); yield 0.15
        T(src + " "); yield 0.25
        got = text().rstrip()
        if want is None:
            note("typed %r" % src, repr(got))
        else:
            check("typing %r gives %r" % (src, want), got == want, repr(got))
    # scene break: is it a list now?
    fresh(); yield 0.1
    T("* * *\nNext scene."); yield 0.3
    note("scene break paragraphs", (para_texts(), [is_listed(i) for i in range(len(para_texts()))]))
    # undo of an autocorrect brings back what was typed
    fresh(); T("teh "); yield 0.2; K("ctrl+z"); yield 0.2
    check("Undo straight after an autocorrect restores what was typed", text() == "teh ", repr(text()))
run_scenarios(a)
