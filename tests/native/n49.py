# W5-20: an ellipsis is a pause, not a full stop.
import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d)))
exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
CASES = [
    ("so... what then ", "So… what then"),
    ("Wait... what? ", "Wait… what?"),
    ("\"Well...\" she said ", "“Well…” she said"),
    ("He paused... and left ", "He paused… and left"),
    ("Well ... fine ", "Well … fine"),
    ("A sentence. Another one ", "A sentence. Another one"),
    ("Mr. smith came ", "Mr. smith came"),
    ("end. new start ", "End. New start"),
    # the third dot converts, as Word does, and the fourth is then an ordinary full stop
    ("dots.... four of them ", "Dots…. Four of them"),
]
def a():
    yield 0.5
    focus()
    for src, want in CASES:
        fresh(); yield 0.2
        T(src); yield 0.35
        got = text().strip()
        check("typing %r gives %r" % (src.strip(), want), got == want, repr(got))
def undo():
    yield 0.3
    fresh(); T("so... "); yield 0.4
    check("the dots became an ellipsis", "…" in text(), repr(text()))
    K("ctrl+z"); yield 0.3
    check("Undo brings the three dots back", "..." in text(), repr(text()))
run_scenarios(a, undo)
