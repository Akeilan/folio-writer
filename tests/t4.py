import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
e = win.engine
def s0():
    e.command(".uno:InsertText", {"Text": "Thiss is a sentense with dialogs. "})
def s1():
    from folio import docapi, bridge
    import sys
    log("bridge mods", [(k, id(v), getattr(v, "ctx", "-")) for k, v in sys.modules.items() if k.endswith("bridge")])
    log("docapi.bridge", id(docapi.bridge))
    m = e.model
    loc = docapi.doc_locale(m)
    log("loc", loc.Language, loc.Country)
    sc = docapi._lingu().getSpellChecker()
    log("sc", sc)
    for w in ("Thiss", "sentense", "dialogs", "house"):
        try:
            log(w, sc.isValid(w, loc, ()))
        except Exception as ex:
            log("ERR", w, repr(ex))
    log("next", docapi.next_misspelling(m, False))
    log("sugg", docapi.suggestions("sentense", loc))
    log("syn", docapi.synonyms("house", loc)[:2])
def s2(): app.quit()
steps(s0, s1, s2, delay=2000)
