import os as _o; TESTS = _o.environ["FOLIO_WRITER_TESTS"]; exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read()); exec(open("/tmp/p5/probes/ph.py").read())
def a():
    yield 0.5
    focus(); fresh(); yield 0.2
    T("Before "); K("alt+equal"); yield 0.6
    x0 = doc_xml()["word/document.xml"]
    note("after alt+=", (cnt(x0, "m:oMath"), ed().story(), win.ribbon.current.name))
    check("Alt+= starts an equation and shows the Equation tab", cnt(x0, "m:oMath") == 1 and win.ribbon.current.name == "Equation", (cnt(x0, "m:oMath"), win.ribbon.current.name))
    T("a^2+b^2=c^2 "); yield 0.5
    x1 = doc_xml()["word/document.xml"]
    check("typing builds up superscripts", cnt(x1, "m:sSup") >= 2, cnt(x1, "m:sSup"))
    shot("eq1")
    for lab, tag in (("Fraction > Stacked Fraction", "m:f"), ("Radical > Square Root", "m:rad"), ("Script > Superscript", "m:sSup"),
                     ("Integral > Integral", "m:nary"), ("Bracket > Parentheses", "m:d"), ("Matrix > 2x2 Empty Matrix", "m:m")):
        before = cnt(doc_xml()["word/document.xml"], tag)
        try:
            R(lab, "Equation")
        except KeyError as e:
            note("no such control", lab); continue
        yield 0.3
        after = cnt(doc_xml()["word/document.xml"], tag)
        check("%s inserts a structure" % lab, after > before, (before, after))
    shot("eq2")
    labs = sorted(l for l, v in _ITEMS.items() if any(t == "Equation" for t, _f in v))
    note("equation labels", labs[:60])
run_scenarios(a)
