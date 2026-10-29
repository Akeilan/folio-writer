import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/t8.py").read().split("items = []")[0])
from folio.keys import BINDINGS
items = []
SKIP = {"close", "new", "read-mode", "focus-mode", "backstage-open", "backstage-print", "save", "save-as", "open-dialog", "toggle-ribbon"}
for spec, act in BINDINGS:
    if isinstance(act, str) and act in SKIP:
        continue
    items.append((spec, lambda a=act: win.run(a)))
log("items", len(items))
fns = [prep, prep2]
for label, fn in items:
    def f(label=label, fn=fn):
        cur[0] = label
        try:
            fn()
        except Exception:
            log("EXC", label, traceback.format_exc().splitlines()[-1])
    fns.append(f)
fns.append(lambda: (log("done"), app.quit()))
steps(*fns, delay=700)
