"""Ink Equation against real handwriting: the CROHME competition data (InkML,
written by many people on tablets). Not shipped; run with a path to the
unpacked data. Reports symbol accuracy (each traceGroup classified alone)
and whole-expression accuracy for simple expressions."""
import collections
import glob
import os
import random
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
NS = "{http://www.w3.org/2003/InkML}"
MAP = {"\\times": "×", "\\div": "÷", "\\pm": "±", "\\sqrt": "√", "-": "−", "\\alpha": "α", "\\beta": "β",
       "\\pi": "π", "\\theta": "θ", "\\sum": "∑", "\\int": "∫", "\\infty": "∞", "\\leq": "≤", "\\geq": "≥",
       "\\neq": "≠", "\\lt": "<", "\\gt": ">", "\\{": "{", "\\}": "}", "\\ldots": "…", "\\cdot": "·",
       "\\gamma": "γ", "\\mu": "μ", "\\sigma": "σ", "\\lambda": "λ", "\\phi": "φ", "\\Delta": "Δ",
       "\\sin": None, "\\cos": None, "\\tan": None, "\\log": None, "\\lim": None, "\\rightarrow": "→",
       "\\prime": "′", "\\exists": "∃", "\\forall": "∀", "\\in": "∈", "COMMA": ","}


def load(path):
    root = ET.parse(path).getroot()
    traces = {}
    for t in root.iter(NS + "trace"):
        pts = []
        for p in (t.text or "").strip().split(","):
            v = p.split()
            if len(v) >= 2:
                try:
                    pts.append((float(v[0]), float(v[1])))
                except ValueError:
                    pass
        traces[t.get("id")] = pts
    truth = None
    for a in root.findall(NS + "annotation"):
        if a.get("type") == "truth":
            truth = (a.text or "").strip().strip("$").strip()
    syms = []
    for tg in root.iter(NS + "traceGroup"):
        ann = tg.find(NS + "annotation")
        refs = [tv.get("traceDataRef") for tv in tg.findall(NS + "traceView")]
        if ann is None or not refs:
            continue
        syms.append((ann.text.strip(), [traces[r] for r in refs if r in traces]))
    return traces, truth, syms


def label(s):
    if s in MAP:
        return MAP[s]
    return s if len(s) == 1 else None


def main(base, n_files=1500, seed=1):
    from folio import inkmath
    files = sorted(glob.glob(os.path.join(base, "**", "*.inkml"), recursive=True))
    files = [f for f in files if "/TestINKMLGT/" in f] or files
    random.Random(seed).shuffle(files)
    files = files[:n_files]
    known = {t[0] for t in inkmath.templates()}
    hit = top3 = total = 0
    per = collections.Counter()
    per_ok = collections.Counter()
    conf = collections.Counter()
    expr_ok = expr_n = 0
    for f in files:
        try:
            traces, truth, syms = load(f)
        except ET.ParseError:
            continue
        for lab, strokes in syms:
            ch = label(lab)
            if ch is None or ch not in known or not strokes:
                continue
            res = inkmath.classify(strokes, 3)
            total += 1
            per[ch] += 1
            if res and res[0][0] == ch:
                hit += 1
                per_ok[ch] += 1
            elif res:
                conf[(ch, res[0][0])] += 1
            if any(c == ch for c, _d in res):
                top3 += 1
        # whole expressions: plain ones (digits, letters, + − = and juxtaposition)
        if truth and re.fullmatch(r"[0-9a-z+\-= ]{1,9}", truth):
            want = truth.replace(" ", "").replace("-", "−")
            got, _ = inkmath.recognise(list(traces.values()))
            expr_n += 1
            if got.replace(" ", "") == want:
                expr_ok += 1
            elif os.environ.get("INK_SHOW"):
                print("   want %-12s got %s" % (want, got))
    print("symbols %d  top-1 %.1f%%  top-3 %.1f%%" % (total, 100.0 * hit / max(1, total), 100.0 * top3 / max(1, total)))
    print("simple expressions %d  exact %.1f%%" % (expr_n, 100.0 * expr_ok / max(1, expr_n)))
    worst = sorted(per, key=lambda c: per_ok[c] / per[c])[:15]
    print("weakest:", ", ".join("%s %d%%" % (c, 100 * per_ok[c] // per[c]) for c in worst if per[c] >= 10))
    print("confusions:", ", ".join("%s→%s %d" % (a, b, n) for (a, b), n in conf.most_common(15)))


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 1500)
