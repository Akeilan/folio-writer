"""Grammar and style checks for the Editor pane, plus readability statistics."""
import re

RULES = [
    # (pattern, message, replacement function or None)
    (re.compile(r"\b(\w+)\s+\1\b", re.I), "Repeated word",
     lambda mm: mm.group(1)),
    (re.compile(r"\b(should|could|would|must|might)\s+of\b", re.I), "Did you mean 'have'?",
     lambda mm: mm.group(1) + " have"),
    (re.compile(r"(?<![\w'])i(?![\w'])"), "Capitalize the pronoun 'I'",
     lambda mm: "I"),
    (re.compile(r"(?<=\S)  +(?=\S)"), "Extra space between words",
     lambda mm: " "),
    (re.compile(r"\s+([,.;:!?])(?=\s|$)"), "Space before punctuation",
     lambda mm: mm.group(1)),
    (re.compile(r"([.!?])\s+([a-z])"), "Capitalize the first word of a sentence",
     lambda mm: mm.group(1) + " " + mm.group(2).upper()),
    (re.compile(r"\b(a)\s+(?=[aeiou]\w)", re.I), "Use 'an' before a vowel sound",
     lambda mm: ("An " if mm.group(1)[0].isupper() else "an ")),
    (re.compile(r"\b(an)\s+(?=[bcdfgjklmnpqrstvwxyz]\w)", re.I),
     "Use 'a' before a consonant sound", lambda mm: ("A " if mm.group(1)[0].isupper() else "a ")),
]
_EXCEPT_AN = re.compile(r"\b(an?)\s+(hour|honest|honor|heir|uni\w*|use\w*|user\w*|one|once|eu\w*)",
                        re.I)


def check(text, lang="en", country="US", gaps=()):
    """[(start, length, message, [suggestions])] for one paragraph. `gaps`
    are where in-line objects (equations, pictures) sit in the text: what
    touches them (the double space around "the value <equation> is") is
    left alone."""
    out = []
    if lang == "en":
        exceptions = {m.start() for m in _EXCEPT_AN.finditer(text)}
        for rx, msg, fix in RULES:
            if msg is None:
                continue
            for mm in rx.finditer(text):
                if "'a'" in msg or "'an'" in msg:
                    if mm.start() in exceptions:
                        continue
                if msg == "Repeated word" and mm.group(1).lower() in ("that", "had"):
                    continue          # "had had", "that that" can be correct
                start, length = mm.start(), mm.end() - mm.start()
                if any(start - 2 <= g <= start + length + 2 for g in gaps):
                    continue
                if any(not (start + length <= s or s + n <= start) for s, n, _m, _x in out):
                    continue
                out.append((start, length, msg, [fix(mm)] if fix else []))
    out.sort()
    return out


# ------------------------------------------------------------ readability
def _syllables(word):
    w = word.lower()
    w = re.sub(r"[^a-z]", "", w)
    if not w:
        return 0
    if len(w) <= 3:
        return 1
    w = re.sub(r"(?:[^laeiouy]es|ed|[^laeiouy]e)$", "", w)
    w = re.sub(r"^y", "", w)
    return max(1, len(re.findall(r"[aeiouy]{1,2}", w)))


def readability(text):
    paras = [p for p in text.split("\n") if p.strip()]
    sentences = [s for s in re.split(r"(?<=[.!?])\s+", " ".join(paras)) if s.strip()]
    words = re.findall(r"[A-Za-z0-9'’-]+", text)
    chars = sum(len(re.sub(r"\W", "", w)) for w in words)
    syl = sum(_syllables(w) for w in words)
    nw, ns, np_ = len(words), max(1, len(sentences)), max(1, len(paras))
    passive = sum(1 for s in sentences if re.search(
        r"\b(am|is|are|was|were|be|been|being)\s+\w+(ed|en)\b", s, re.I))
    fre = 206.835 - 1.015 * (nw / ns) - 84.6 * (syl / max(1, nw))
    fk = 0.39 * (nw / ns) + 11.8 * (syl / max(1, nw)) - 15.59
    return {
        "Words": nw, "Characters": chars, "Paragraphs": len(paras),
        "Sentences": len(sentences),
        "Sentences per Paragraph": round(len(sentences) / np_, 1),
        "Words per Sentence": round(nw / ns, 1),
        "Characters per Word": round(chars / max(1, nw), 1),
        "Passive Sentences": "%d%%" % round(100.0 * passive / ns),
        "Flesch Reading Ease": round(max(0.0, min(100.0, fre)), 1),
        "Flesch-Kincaid Grade Level": round(max(0.0, fk), 1),
    }
