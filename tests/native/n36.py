import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
# 2.31: every ribbon icon is Folio's own artwork (W2-06): an own SVG or the drawn set in wicons.py
import os
from folio import icons as I
from folio import wicons


def names():
    out = set()
    for c in win.ribbon.controls:
        n = getattr(c, "icon_name", None)
        if isinstance(n, str):
            out.add(n)
        m = getattr(c, "menu", None)
        if isinstance(m, list):
            for it in m:
                if isinstance(it, tuple) and len(it) > 2 and isinstance(it[2], str):
                    out.add(it[2])
    return out


def own(n):
    base = n.replace(".uno:", "").lower()
    return os.path.exists(os.path.join(I.OWN, base + ".svg")) or I.drawn_name(base) is not None


def a():
    yield 0.5
    ns = names()
    check("ribbon has icons", len(ns) > 150, len(ns))
    missing = sorted(n for n in ns if not own(n))
    check("every ribbon icon is Folio's own", not missing, missing)
    bad = []
    for n in sorted(wicons.ICONS):
        for size in (16, 32):
            pb = I.drawn(n, size)
            if pb is None or pb.get_width() != size:
                bad.append((n, size))
                continue
            px = pb.get_pixels()
            if not any(px[i + 3] for i in range(0, len(px), 4)):
                bad.append((n, size, "blank"))
    check("every drawn icon renders at 16 and 32 px", not bad, bad[:10])
    pb = I.pixbuf("bold", 32)
    check("pixbuf() uses the drawn set", pb is not None and pb.get_width() == 32)


run_scenarios(a)
