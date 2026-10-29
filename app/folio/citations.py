"""Citations & Bibliography: sources, in-text citations in APA / MLA / Chicago /
IEEE style, and a bibliography that formats itself in the same style.

Citations are the engine's bibliography fields; the source's tag is kept in
the field's Custom1 entry so a citation can be re-rendered when the style or
the source changes. Sources that aren't cited yet live in a document property
and in the user's master list (~/.config/folio-writer/sources.json)."""
import json
import os
import re


STYLES = ["APA", "Chicago", "Harvard", "IEEE", "ISO 690", "MLA", "Turabian"]
# in-text behaviour follows a related style
BASE = {"Harvard": "APA", "Turabian": "Chicago", "ISO 690": "Chicago"}

# Word-style source types -> engine bibliography type
TYPES = [("Book", 1), ("Book Section", 4), ("Journal Article", 0),
         ("Article in a Periodical", 0), ("Conference Proceedings", 6), ("Report", 13),
         ("Web site", 16), ("Document From Web site", 16), ("Miscellaneous", 10)]

# which entry boxes each type shows: (key, label)
FIELDS = {
    "Book": [("author", "Author"), ("title", "Title"), ("year", "Year"), ("city", "City"),
             ("publisher", "Publisher")],
    "Book Section": [("author", "Author"), ("title", "Title"), ("booktitle", "Book Title"),
                     ("editor", "Editor"), ("year", "Year"), ("pages", "Pages"),
                     ("city", "City"), ("publisher", "Publisher")],
    "Journal Article": [("author", "Author"), ("title", "Title"), ("journal", "Journal Name"),
                        ("year", "Year"), ("volume", "Volume"), ("issue", "Issue"),
                        ("pages", "Pages")],
    "Article in a Periodical": [("author", "Author"), ("title", "Title"),
                                ("journal", "Periodical Title"), ("year", "Year"),
                                ("month", "Month"), ("pages", "Pages")],
    "Conference Proceedings": [("author", "Author"), ("title", "Title"),
                               ("booktitle", "Conference Name"), ("year", "Year"),
                               ("pages", "Pages"), ("city", "City"),
                               ("publisher", "Publisher")],
    "Report": [("author", "Author"), ("title", "Title"), ("year", "Year"),
               ("publisher", "Publisher"), ("city", "City")],
    "Web site": [("author", "Author"), ("title", "Name of Web Page"),
                 ("journal", "Name of Web Site"), ("year", "Year"), ("url", "URL")],
    "Document From Web site": [("author", "Author"), ("title", "Name of Web Page"),
                               ("journal", "Name of Web Site"), ("year", "Year"),
                               ("url", "URL")],
    "Miscellaneous": [("author", "Author"), ("title", "Title"), ("year", "Year"),
                      ("publisher", "Publisher"), ("city", "City")],
}


MASTER = os.path.join(os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config"),
                      "folio-writer", "sources.json")


# ------------------------------------------------------------------ authors
def authors(src):
    """'Smith, John; Jones, Ann' -> [('Smith', 'John'), ('Jones', 'Ann')]"""
    out = []
    for a in re.split(r"\s*;\s*|\s+and\s+", (src.get("author") or "").strip()):
        if not a:
            continue
        if "," in a:
            last, first = [x.strip() for x in a.split(",", 1)]
        else:
            parts = a.split()
            last, first = parts[-1], " ".join(parts[:-1])
        out.append((last, first))
    return out


def _initials(first):
    return " ".join(p[0] + "." for p in first.replace("-", " ").split() if p)


def author_list(src, style):
    a = authors(src)
    if not a:
        return src.get("title", "")
    if style == "Harvard":
        names = ["%s, %s" % (l, _initials(f)) if f else l for l, f in a]
        return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]
    if style == "ISO 690":
        names = ["%s, %s" % (l.upper(), f) if f else l.upper() for l, f in a]
        return " and ".join(names) if len(names) <= 2 else "; ".join(names)
    style = BASE.get(style, style)
    if style == "APA":
        names = ["%s, %s" % (l, _initials(f)) if f else l for l, f in a]
        if len(names) == 1:
            return names[0]
        return ", ".join(names[:-1]) + ", & " + names[-1]
    if style == "MLA":
        l, f = a[0]
        first = "%s, %s" % (l, f) if f else l
        if len(a) == 1:
            return first
        if len(a) == 2:
            l2, f2 = a[1]
            return "%s, and %s" % (first, ("%s %s" % (f2, l2)).strip())
        return first + ", et al."
    if style == "IEEE":
        names = [("%s %s" % (_initials(f), l)).strip() for l, f in a]
        if len(names) == 1:
            return names[0]
        return ", ".join(names[:-1]) + " and " + names[-1]
    # Chicago
    l, f = a[0]
    names = ["%s, %s" % (l, f) if f else l] + [("%s %s" % (f2, l2)).strip() for l2, f2 in a[1:]]
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + ", and " + names[-1]


def citation_text(src, style):
    """What appears in the text, without the brackets."""
    orig = style
    style = BASE.get(style, style)
    a = authors(src)
    year = src.get("year") or "n.d."
    if a:
        if len(a) == 1:
            who = a[0][0]
        elif len(a) == 2:
            who = "%s %s %s" % (a[0][0], "&" if orig == "APA" else "and", a[1][0])
        else:
            who = a[0][0] + " et al."
    else:
        who = src.get("title", "Untitled")
    if style == "APA":
        return "%s, %s" % (who, year)
    if style == "MLA":
        return who
    if style == "Chicago":
        return "%s %s" % (who, year)
    return src.get("tag", who)


def cite_label(src, style, base, opts):
    """The in-text label for one citation: the source's label (base), with
    the citation's own page numbers and suppressed parts."""
    opts = opts or {}
    style = BASE.get(style, style)
    sup = set(opts.get("suppress") or ())
    pages = (opts.get("pages") or "").strip()
    if style == "IEEE":
        lab = base
        return lab + (", p. %s" % pages if pages else "")
    a = authors(src)
    who = base
    year = src.get("year") or "n.d."
    if style in ("APA", "Chicago"):
        # base is "Who, Year" (APA) or "Who Year" (Chicago), maybe with a/b suffix
        sep = ", " if style == "APA" else " "
        if sep in base:
            who, year = base.rsplit(sep, 1)
        parts = []
        if "author" not in sup:
            parts.append(who)
        if "year" not in sup:
            parts.append(year)
        if not parts and "title" not in sup:
            parts.append(src.get("title", ""))
        lab = sep.join(p for p in parts if p)
        if pages:
            lab += (", p. %s" if style == "APA" else ", %s") % pages
        return lab
    # MLA: (Author page)
    lab = "" if "author" in sup else who
    if pages:
        lab = (lab + " " + pages).strip()
    return lab or (src.get("title", "") if "title" not in sup else "")


def make_tag(src, existing=()):
    a = authors(src)
    base = (a[0][0] if a else (src.get("title") or "Src"))[:3]
    base = re.sub(r"\W", "", base) or "Src"
    tag = base + (src.get("year") or "")[-2:]
    out, n = tag, 1
    while out in existing:
        n += 1
        out = "%s%d" % (tag, n)
    return out


# ------------------------------------------------------------------ entry formatting
def entry_parts(src, style):
    """The bibliography entry as [(text, italic)] (also used for the preview)."""
    t = src.get("type", "Book")
    A = author_list(src, style)
    y = src.get("year") or "n.d."
    title = src.get("title", "")
    pub = src.get("publisher", "")
    city = src.get("city", "")
    j = src.get("journal", "")
    vol, iss, pages = src.get("volume", ""), src.get("issue", ""), src.get("pages", "")
    url = src.get("url", "")
    book = src.get("booktitle", "")
    ed = src.get("editor", "")
    out = []

    def add(text, italic=False):
        if text:
            out.append((text, italic))
    article = t in ("Journal Article", "Article in a Periodical")
    web = t in ("Web site", "Document From Web site")
    if style == "Turabian":
        style = "Chicago"
    if style in ("Harvard", "ISO 690"):
        harvard = style == "Harvard"
        add(("%s (%s) " if harvard else "%s. %s. ") % (A, y))
        if article:
            add(title + ". " if harvard else title + ". ")
            add(j, True)
            add("%s%s%s." % (", " + vol if vol else "", "(%s)" % iss if iss else "",
                             (", pp. " if harvard else ", ") + pages if pages else ""))
        elif web:
            add(title, True)
            add(". [Online]. " if not harvard else ". ")
            add(("Available at: %s" if harvard else "Available from: %s") % url if url else "")
        elif t in ("Book Section", "Conference Proceedings"):
            add(title + ". In: ")
            add(book, True)
            add(". %s%s." % (city + ": " if city else "", pub))
        else:
            add(title, True)
            add(". %s%s." % (city + ": " if city else "", pub) if (pub or city) else ".")
        if out:
            t0, it = out[-1]
            out[-1] = (t0.rstrip(), it)
        return out
    if style == "APA":
        add("%s (%s). " % (A, y))
        if article:
            add(title + ". ")
            add(j, True)
            if vol:
                add(", ")
                add(vol, True)
            if iss:
                add("(%s)" % iss)
            if pages:
                add(", " + pages)
            add(".")
        elif t == "Book Section" or t == "Conference Proceedings":
            add(title + ". ")
            add("In %s%s, " % (ed, " (Ed.)" if ed else "") if ed else "In ")
            add(book, True)
            if pages:
                add(" (pp. %s)" % pages)
            add(". " + pub + "." if pub else ".")
        elif web:
            add(title, True)
            add(". ")
            if j:
                add(j + ". ")
            add(url)
        else:
            add(title, True)
            add(". ")
            add(pub + "." if pub else "")
    elif style == "MLA":
        add(A + ". ")
        if article:
            add("“%s.” " % title)
            add(j, True)
            bits = [b for b in ("vol. " + vol if vol else "", "no. " + iss if iss else "",
                                y, "pp. " + pages if pages else "") if b]
            add(", " + ", ".join(bits) + "." if bits else ".")
        elif web:
            add("“%s.” " % title)
            add(j, True)
            add(", %s, %s." % (y, url) if url else ", %s." % y)
        elif t in ("Book Section", "Conference Proceedings"):
            add("“%s.” " % title)
            add(book, True)
            add(", %s%s, %s%s." % ("edited by %s, " % ed if ed else "", pub, y,
                                    ", pp. " + pages if pages else ""))
        else:
            add(title, True)
            add(". %s, %s." % (pub, y) if pub else ". %s." % y)
    elif style == "Chicago":
        add("%s. %s. " % (A, y))
        if article:
            add("“%s.” " % title)
            add(j, True)
            add(" %s%s%s." % (vol, " (%s)" % iss if iss else "", ": " + pages if pages else ""))
        elif web:
            add("“%s.” " % title)
            add(j + ". " if j else "")
            add(url + "." if url else "")
        else:
            add(title, True)
            add(". %s%s." % (city + ": " if city else "", pub) if (pub or city) else ".")
    else:  # IEEE
        add("%s, " % A)
        if article:
            add("“%s,” " % title)
            add(j, True)
            bits = [b for b in ("vol. " + vol if vol else "", "no. " + iss if iss else "",
                                "pp. " + pages if pages else "", y) if b]
            add(", " + ", ".join(bits) + ".")
        elif web:
            add("“%s.” " % title)
            add(j + ". " if j else "")
            add("[Online]. Available: " + url if url else "")
        else:
            add(title, True)
            where = (city + ": " if city and pub else city) + pub
            add(". " + ", ".join(b for b in (where, y) if b) + ".")
    if out:
        t, it = out[-1]
        out[-1] = (t.rstrip(), it)
    return out


def entry_text(src, style):
    return "".join(t for t, _i in entry_parts(src, style))


# ------------------------------------------------------------------ storage
def _load_master():
    try:
        with open(MASTER, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return []


def master_sources():
    return _load_master()


def save_master(sources):
    os.makedirs(os.path.dirname(MASTER), exist_ok=True)
    tmp = MASTER + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(sources, f, indent=1, ensure_ascii=False)
    os.replace(tmp, MASTER)


def add_to_master(src):
    ms = [s for s in _load_master() if s.get("tag") != src.get("tag")]
    ms.append(src)
    save_master(ms)


def _identifiers(m, sources, style):
    """Unique in-text labels; same author and year get 2020a, 2020b (APA)."""
    labels = {}
    seen = {}
    for s in sources:
        lab = citation_text(s, style)
        seen.setdefault(lab, []).append(s["tag"])
    for lab, tags in seen.items():
        if len(tags) == 1 or BASE.get(style, style) in ("MLA", "IEEE"):
            for t in tags:
                labels[t] = lab if style != "IEEE" else t
        else:
            for i, t in enumerate(tags):
                labels[t] = lab + "abcdefghijklmnopqrstuvwxyz"[i % 26]
    return labels


def _sort_key(src):
    a = authors(src)
    return ((a[0][0] if a else src.get("title", "")).lower(), src.get("year", ""),
            src.get("title", "").lower())


