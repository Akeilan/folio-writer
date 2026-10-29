"""AutoFormat (W3-09): the whole document formatted at once, as Word's AutoFormat Now
(Ctrl+Alt+K) and the AutoFormat dialog do, and "Define styles based on your formatting"
(AutoFormat As You Type).

AutoFormat follows the AutoFormat tab of the AutoCorrect dialog: built-in heading styles,
list styles, automatic bulleted lists, other paragraph styles (Body Text), smart quotes,
ordinals, fractions, dashes, *bold* and _italic_, internet paths, and Preserve styles."""
import re

BODY = 10
OPTIONS = [
    ("#", "Apply", None),
    ("af_headings", "Built-in Heading styles", True),
    ("af_list_styles", "List styles", True),
    ("af_bullets", "Automatic bulleted lists", True),
    ("af_other_styles", "Other paragraph styles", True),
    ("#", "Replace", None),
    ("af_quotes", "\"Straight quotes\" with “smart quotes”", True),
    ("af_ordinals", "Ordinals (1st) with superscript", True),
    ("af_fractions", "Fractions (1/2) with fraction character (½)", True),
    ("af_dashes", "Hyphens (--) with dash (—)", True),
    ("af_bold_italic", "*Bold* and _italic_ with real formatting", True),
    ("af_urls", "Internet and network paths with hyperlinks", True),
    ("#", "Preserve", None),
    ("af_preserve", "Styles", True),
]
FRACTIONS = {"1/2": "½", "1/4": "¼", "3/4": "¾"}
BULLET = re.compile(r"^([*•>-]|->|o)\s+")
NUMBER = re.compile(r"^(\(?)(\d{1,3}|[a-z]|[A-Z])([.)])\s+")
NUMBERED_HEADING = re.compile(r"^(\d+(?:\.\d+){0,2})\.?\s+\S")


def defaults():
    return {k: d for k, _l, d in OPTIONS if k != "#"}


def _style_ids(ed):
    return {name: sid for sid, name in ed.paragraph_styles()}


def _ensure_style(ed, name, based="Normal", after=None):
    ids = _style_ids(ed)
    if name in ids:
        return ids[name]
    sid = ed.create_style(name, "paragraph", ids.get(based))
    if after is not None:
        ed.style_apply_para(sid, [("w:spacing", [("w:after", str(after))])])
    return sid


def _heading_like(text):
    t = text.strip()
    words = t.split()
    return (0 < len(words) <= 10 and t[:1].isalnum() and t[:1] == t[:1].upper()
            and t[-1:] not in ".!?:;," and not t.startswith(("http", "www")))


def _set_style(ed, node, sid):
    ed.select_nodes(node, 0, node, 0)
    ed.set_style(sid)


def _replace(ed, node, a, b, new):
    ed.select_nodes(node, a, node, b)
    if new:
        ed.type_text(new)
    else:
        ed.delete(True, False)


def _texts(ed):
    return [(r[0], r[1], r[2], r[3], r[4]) for r in ed.outline_paras()]   # node, text, level, size, bold


def run(ed, opts=None):
    """AutoFormat the document (one undo step). Returns {kind: count}."""
    o = defaults()
    o.update(opts or {})
    done = {}

    def count(k):
        done[k] = done.get(k, 0) + 1
    in_table = set()
    for kind, node, ti in ed.body_blocks():
        if kind != "p":
            try:
                for row in ed.table_cells(ti):
                    for cell in row:
                        in_table.update(cell)
            except Exception:
                pass
    styles = {name: sid for sid, name in ed.paragraph_styles()}
    normal_like = {"Normal", "Body Text", "Plain Text", ""}
    ed.begin_group("AutoFormat")
    try:
        paras = _texts(ed)
        nodes = [p[0] for p in paras]
        for i, (node, text, level, _size, _bold) in enumerate(paras):
            if node in in_table or not text.strip():
                continue
            ed.select_nodes(node, 0, node, 0)
            st = (ed.state() or {}).get("style", "")
            in_list = ed.list_info() is not None
            plain = st in normal_like and (st in ("Normal", "") or not o["af_preserve"])
            nxt = paras[i + 1][1] if i + 1 < len(paras) else ""
            # ---- lists typed with "*" or "1." at the start
            m = BULLET.match(text)
            if m and plain and not in_list and o["af_bullets"]:
                _replace(ed, node, 0, m.end(), "")
                ed.select_nodes(node, 0, node, 0)
                ed.toggle_list("bullet")
                count("bulleted lists")
                text = text[m.end():]
                in_list = True
            m = NUMBER.match(text)
            nh = NUMBERED_HEADING.match(text)
            if m and plain and not in_list and o["af_list_styles"] and not (nh and _heading_like(text)):
                opn, mark, close = m.groups()
                if mark.isdigit():
                    fmt, start = "decimal", int(mark)
                else:
                    fmt = "lowerLetter" if mark.islower() else "upperLetter"
                    start = ord(mark.lower()) - 96
                _replace(ed, node, 0, m.end(), "")
                ed.select_nodes(node, 0, node, 0)
                ed.toggle_list("number")
                try:
                    ed.set_list_format(fmt, ("(" if opn else "") + "%1" + close, None, start)
                except Exception:
                    pass
                count("numbered lists")
                text = text[m.end():]
                in_list = True
            # ---- headings: a short line on its own followed by text
            if o["af_headings"] and plain and not in_list and _heading_like(text) and nxt.strip() \
                    and not _heading_like(nxt) and len(nxt.split()) > len(text.split()):
                depth = nh.group(1).count(".") + 1 if nh else 1
                sid = styles.get("Heading %d" % depth) or _ensure_style(ed, "Heading %d" % depth)
                _set_style(ed, node, sid)
                count("headings")
                text = ed.para_text_of(node)
            elif o["af_other_styles"] and plain and not in_list and st in ("Normal", "") \
                    and len(text.split()) > 10:
                sid = _ensure_style(ed, "Body Text", "Normal", after=120)
                _set_style(ed, node, sid)
                count("body text")
            # ---- replacements in the text
            _replace_text(ed, node, o, count)
    finally:
        ed.end_group()
    return done


def _replace_text(ed, node, o, count):
    text = ed.para_text_of(node)
    edits = []          # (a, b, new, kind, extra)
    if o["af_quotes"]:
        for m in re.finditer(r"[\"']", text):
            k = m.start()
            prev = text[k - 1] if k else " "
            ch = m.group()
            if ch == '"':
                new = "“" if prev in " \t([{—–-“‘" else "”"
            else:
                new = "’" if prev.isalnum() else ("‘" if prev in " \t([{—–-“" else "’")
            edits.append((k, k + 1, new, "quotes", None))
    if o["af_dashes"]:
        for m in re.finditer(r"(\w)( ?)--( ?)(?=\w)", text):
            spaced = bool(m.group(2) or m.group(3))
            edits.append((m.start(2), m.end(3), " – " if spaced else "—", "dashes", None))
    if o["af_fractions"]:
        for m in re.finditer(r"(?<![\d/])(1/2|1/4|3/4)(?![\d/])", text):
            edits.append((m.start(), m.end(), FRACTIONS[m.group()], "fractions", None))
    # no overlapping edits, from the end so offsets hold
    edits.sort(key=lambda e: e[0])
    kept = []
    end = -1
    for e in edits:
        if e[0] >= end:
            kept.append(e)
            end = e[1]
    for a, b, new, kind, _x in reversed(kept):
        _replace(ed, node, a, b, new)
        count(kind)
    text = ed.para_text_of(node)
    if o["af_bold_italic"]:
        for m in reversed(list(re.finditer(r"(?<![\w*])\*(\S(?:[^*]*\S)?)\*(?![\w*])|(?<![\w_])_(\S(?:[^_]*\S)?)_(?![\w_])", text))):
            inner = m.group(1) or m.group(2)
            bold = m.group(1) is not None
            a = m.start()
            _replace(ed, node, a, m.end(), inner)
            ed.select_nodes(node, a, node, a + len(inner))
            ed.apply_run([("w:b" if bold else "w:i", [])], "AutoFormat")
            count("bold" if bold else "italic")
        text = ed.para_text_of(node)
    if o["af_ordinals"]:
        for m in reversed(list(re.finditer(r"\b\d+(st|nd|rd|th)\b", text))):
            ed.select_nodes(node, m.start(1), node, m.end(1))
            ed.apply_run([("w:vertAlign", [("w:val", "superscript")])], "AutoFormat")
            count("ordinals")
    if o["af_urls"]:
        for m in reversed(list(re.finditer(r"(?<![\w@/])((?:https?://|www\.)[^\s<>\"]+[^\s<>\".,;:!?)]|[\w.+-]+@[\w-]+\.[\w.]*\w)", text))):
            url = m.group(1)
            target = url if "://" in url else ("mailto:" + url if "@" in url else "http://" + url)
            if ed.select_nodes(node, m.start(1), node, m.end(1)):
                if not ed.link_at_caret():
                    ed.insert_hyperlink(target, url)
                    count("links")
    ed.select_nodes(node, 0, node, 0)


# ------------------------------------------------------------------ as you type
def define_style(ed, node):
    """Define styles based on your formatting: a short line formatted by hand (bold or
    larger type) becomes a heading whose style takes that formatting."""
    text = ed.para_text_of(node).strip()
    if not _heading_like(text):
        return None
    ed.select_nodes(node, 0, node, len(ed.para_text_of(node)))
    s = ed.state() or {}
    if s.get("style") not in ("Normal", "Body Text", "") or ed.list_info() is not None:
        ed.select_nodes(node, len(ed.para_text_of(node)), node, len(ed.para_text_of(node)))
        return None
    ids = _style_ids(ed)
    base = ed.style_run_values(ids.get(s.get("style") or "Normal", "Normal")) if ids else {}
    try:
        base_size = float(base.get("size") or 0) or 11.0
    except (TypeError, ValueError):
        base_size = 11.0
    size = float(s.get("size") or base_size)
    bold = s.get("bold") is True
    if not ((bold and not base.get("bold")) or size >= base_size + 2):
        ed.select_nodes(node, len(ed.para_text_of(node)), node, len(ed.para_text_of(node)))
        return None
    level = 1 if size >= base_size + 5 else 2 if size >= base_size + 3 else 3
    name = "Heading %d" % level
    sid = ids.get(name) or _ensure_style(ed, name)
    edits = [("w:sz", [("w:val", str(int(round(size * 2))))]), ("w:szCs", [("w:val", str(int(round(size * 2))))])]
    edits.append(("w:b", [] if bold else [("w:val", "0")]))
    edits.append(("w:i", [] if s.get("italic") is True else [("w:val", "0")]))
    if s.get("font"):
        edits.append(("w:rFonts", [("w:ascii", s["font"]), ("w:hAnsi", s["font"]), ("w:cs", s["font"])]))
    if s.get("color") and s.get("color") != "auto":
        edits.append(("w:color", [("w:val", s["color"])]))
    ed.begin_group("AutoFormat")
    try:
        ed.style_apply_run(sid, edits)
        ed.set_style(sid)
        ed.clear_formatting()
    finally:
        ed.end_group()
    end = len(ed.para_text_of(node))
    ed.select_nodes(node, end, node, end)
    return name
