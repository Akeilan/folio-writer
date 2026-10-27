exec(open("/home/claude/folio2/tests/common.py").read())
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
