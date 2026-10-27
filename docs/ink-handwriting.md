# Ink Equation on real handwriting (W-10)

Measured with `tools/ink_eval.py` on the CROHME 2013 test set (671 expressions written
on pen tablets by writers whose handwriting the recogniser never saw).

| | Before (font shapes only) | After (2.30.0) |
|---|---|---|
| Symbols, first guess right | 47.6% | 77.9% |
| Symbols, right answer in the first three | 65.9% | 93.1% |
| Simple expressions (digits, letters, + − =) exactly right | 0% | 64.3% |

What changed: `share/inkmath/handwriting.json` adds 2,414 handwritten shapes for 95
symbols, learnt by `tools/build_ink_handwriting.py` from the CROHME 2011–2013 training
data (k-means over the same features the recogniser uses). The shapes from the Hershey
fonts stay as a fallback. Common symbols win ties against rare look-alikes, and context
now reads a cross between letters as x and a short-stemmed t between operands as +.

The remaining misses are mostly look-alikes that need the user's eye anyway (x/X, 1/|,
P/p, S/s, o/0); the corrections panel offers the alternatives. The CROHME data itself is
not in this repository.
