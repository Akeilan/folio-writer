"""Builds share/inkmath/templates.json for Ink Equation from the Hershey
vector fonts (public-domain glyph data; read with the MIT-licensed
Hershey-Fonts package: pip install Hershey-Fonts)."""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "app"))
from folio.inkfeatures import aspect, features, transform  # noqa: E402

from HersheyFonts import HersheyFonts  # noqa: E402

MATHLOW = {"!": "±", "#": "×", "$": "·", "&": "≤", "'": "≥", "(": "(", ")": ")",
           "+": "+", ",": ",", "/": "/", ":": "∏", ";": "∑", "<": "<", "=": "=",
           ">": ">", "?": "≠", "[": "[", "]": "]", "_": "∞", "b": "√", "c": "√",
           "o": "√", "i": "→", "m": "∂", "n": "∇", "p": "∫", "q": "∫", "r": "(",
           "s": ")", "x": "÷", "{": "{", "}": "}", "e": "∪", "g": "∩", "h": "∈"}
GREEK = {"a": "α", "b": "β", "d": "δ", "e": "ε", "f": "φ", "g": "γ", "h": "η",
         "l": "λ", "m": "μ", "p": "π", "q": "θ", "r": "ρ", "s": "σ", "t": "τ", "w": "ω",
         "D": "Δ", "Q": "θ", "S": "Σ", "W": "Ω", "F": "Φ", "P": "Π", "y": "ψ"}
LATIN_FONTS = ["futural", "futuram", "rowmans", "scripts", "scriptc", "timesi", "cursive",
               "timesr"]
UPPER_FONTS = ["futural", "rowmans", "timesi", "scripts"]
DIGIT_FONTS = ["futural", "futuram", "rowmans", "scripts", "timesi", "timesr"]
PLAIN_SYMBOLS = "+-=()[]/<>!"


def strokes(font, ch):
    f = FONTS[font]
    return [list(map(tuple, s)) for s in f.strokes_for_text(ch) if len(s) >= 1]


FONTS = {}


def load(name):
    f = HersheyFonts()
    f.load_default_font(name)
    FONTS[name] = f


def main():
    for n in set(LATIN_FONTS + UPPER_FONTS + DIGIT_FONTS + ["mathlow", "greek"]):
        load(n)
    samples = []
    for ch in "abcdefghijklmnopqrstuvwxyz":
        for font in LATIN_FONTS:
            samples.append((ch, strokes(font, ch)))
    for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        for font in UPPER_FONTS:
            samples.append((ch, strokes(font, ch)))
    for ch in "0123456789":
        for font in DIGIT_FONTS:
            samples.append((ch, strokes(font, ch)))
    for ch in PLAIN_SYMBOLS:
        for font in ("futural", "rowmans"):
            samples.append(("−" if ch == "-" else ch, strokes(font, ch)))
    for key, ch in MATHLOW.items():
        samples.append((ch, strokes("mathlow", key)))
    for key, ch in GREEK.items():
        samples.append((ch, strokes("greek", key)))
    out = []
    for ch, st in samples:
        if not st or not any(len(s) > 1 for s in st):
            continue
        for slant, rot, sx in ((0, 0, 1), (0.2, 0, 1), (-0.1, 0.06, 1), (0, -0.07, 0.85),
                               (0.1, 0.04, 1.15)):
            t = transform(st, slant, rot, sx)
            out.append({"c": ch, "n": len(st), "a": round(aspect(t), 3),
                        "f": [round(v, 2) for v in features(t)]})
    path = os.path.join(HERE, "..", "share", "inkmath", "templates.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump(out, fh, separators=(",", ":"))
    print(len(out), "templates", os.path.getsize(path) // 1024, "KB")


if __name__ == "__main__":
    main()
