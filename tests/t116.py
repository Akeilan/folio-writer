import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
import collections
def s0():
    ctr = win.ribbon.catalog() if hasattr(win.ribbon,"catalog") else None
    from folio import customize
    items = customize.catalog(win) if hasattr(customize,"catalog") else []
    by = collections.defaultdict(list)
    for key,(label, icon, c) in items.items():
        by[(key.split("|")[0], icon)].append(label)
    for (tab, icon), labels in sorted(by.items()):
        if len(set(labels)) >= 3:
            log(tab, icon, len(set(labels)), "|".join(sorted(set(labels)))[:200])
    app.quit()
steps(s0, delay=3000)
