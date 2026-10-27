"""Builds share/inkmath/handwriting.json: shapes of handwritten symbols for
Ink Equation, learnt from the CROHME competition's training data (many
writers on pen tablets): per symbol, up to 24 typical shapes (k-means over
the same features the recogniser uses). The test set stays out, so
tools/ink_eval.py measures writers the shapes never saw.

    python3 tools/build_ink_handwriting.py /path/to/CROHME_full_v2
"""
import collections
import glob
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "app"))
sys.path.insert(0, HERE)
from folio.inkfeatures import aspect, features  # noqa: E402
from ink_eval import label, load  # noqa: E402


def kmeans(X, k, iters=25, seed=0):
    rng = np.random.default_rng(seed)
    C = X[rng.choice(len(X), k, replace=False)]
    for _ in range(iters):
        d = X @ C.T
        a = d.argmax(1)
        for j in range(k):
            m = X[a == j]
            if len(m):
                c = m.mean(0)
                C[j] = c / (np.linalg.norm(c) or 1)
    return C, np.bincount((X @ C.T).argmax(1), minlength=k)


def main(base):
    files = [f for f in glob.glob(os.path.join(base, "**", "*.inkml"), recursive=True)
             if "train" in f.lower() and "Test" not in f]
    data = collections.defaultdict(list)
    for i, f in enumerate(files):
        try:
            _t, _truth, syms = load(f)
        except Exception:
            continue
        for lab, strokes in syms:
            ch = label(lab)
            if ch is None or not strokes or not any(strokes):
                continue
            strokes = [s for s in strokes if s]
            data[ch].append((features(strokes), aspect(strokes), len(strokes)))
        if i % 1000 == 0:
            print(i, "/", len(files), file=sys.stderr)
    out = []
    for ch, items in sorted(data.items()):
        if len(items) < 12:
            continue
        X = np.array([it[0] for it in items], dtype=float)
        X /= np.linalg.norm(X, axis=1, keepdims=True).clip(1e-9)
        k = int(min(48, max(2, len(items) // 15)))
        C, counts = kmeans(X, k)
        assign = (X @ C.T).argmax(1)
        for j in range(k):
            members = [items[i] for i in np.nonzero(assign == j)[0]]
            if len(members) < 3:
                continue
            a = float(np.median([m[1] for m in members]))
            n = int(np.median([m[2] for m in members]))
            out.append({"c": ch, "n": n, "a": round(a, 3), "f": [round(float(v), 4) for v in C[j]]})
    dst = os.path.join(HERE, "..", "share", "inkmath", "handwriting.json")
    with open(dst, "w") as fh:
        json.dump(out, fh, separators=(",", ":"))
    print(len(out), "shapes for", len({o["c"] for o in out}), "symbols ->", dst)


if __name__ == "__main__":
    main(sys.argv[1])
