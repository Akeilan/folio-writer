exec(open("/home/claude/folio2/tests/common.py").read())
import sys
def s0():
    from folio import grammar
    grammar._proofreader()
    hits = [(n, m) for n, m in list(sys.modules.items()) if m is not None and ("ightproof" in n or hasattr(m, "Lightproof"))]
    log("modules", [n for n, _ in hits], [n for n in sys.modules if "proof" in n.lower() or "pymodule" in n.lower() or "vnd" in n.lower()][:20])
    for n, mod in hits:
        log(n, mod.Lightproof, getattr(mod.Lightproof, "doProofreading", None))
    app.quit()
steps(lambda: None, s0, delay=3000)
