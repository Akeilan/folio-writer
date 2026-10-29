import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
def lists():
    for inp, label in (("a) ", "a)"), ("A. ", "A."), ("i. ", "i."), ("I. ", "I."), ("c) ", "c)"), ("(a) ", "(a)"), ("(1) ", "(1)")):
        fresh(); yield 0.4
        K("ctrl+shift+n"); yield 0.2
        T(inp + "item"); yield 0.8
        K("Return"); T("next"); yield 0.8
        p = para_texts()
        info = [(t, list_label(i)) for i, t in enumerate(p)]
        check("autolist %r" % inp, len(p) == 2 and p[0] in ("Item", "item"), info)
        check("autolist label %r" % inp, list_label(0) == label, info)
    fresh(); yield 0.4
    T("> arrow"); K("Return"); T("next"); yield 0.8
    p = para_texts()
    check("> starts arrow bullet", is_listed(0) and p[0].lower() == "arrow", [(t, list_label(i)) for i, t in enumerate(p)])
    shot("r3_arrow")
    fresh(); yield 0.4
    T("Ann said a) was fine"); yield 0.6
    check("mid-sentence a) untouched", text() == "Ann said a) was fine", repr(text()))
def rule():
    fresh(); yield 0.4
    T("Before"); K("Return"); K("minus", "minus", "minus"); K("Return"); yield 0.8
    info = [(t, border("bottom", i)) for i, t in enumerate(para_texts())]
    check("--- Enter draws a line", bool(info[0][1]) and all(t == "" for t, _w in info[1:]), info)
    shot("r3_rule")
def comment():
    win.open_file("/tmp/wfid/fid.docx"); yield 5.0
    labs = [w.get_text() for w in find_widget(win, lambda w: isinstance(w, Gtk.Label) and w.get_text() == "Reviewer note")]
    check("imported comment shows its text", bool(labs), labs)
run_scenarios(lists, rule, comment)
