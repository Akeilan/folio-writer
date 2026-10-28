# Word-parity helpers over Folio's own engine (exec'd by wc.py). The scenarios read the
# document the way Writer itself does: paragraphs are engine nodes, positions are
# (node, offset), formatting is the engine's run_values()/para_values().
ED = E.ed


def ed():
    return E.ed


def blocks():
    """Body blocks in order: ("p", node, None) or ("t", node, table_index)."""
    return list(E.ed.body_blocks())


def all_paras():
    """Body paragraphs in order, a table's cells' paragraphs in its place."""
    out = []
    for kind, node, ti in E.ed.body_blocks():
        if kind == "p":
            out.append(node)
        else:
            for row in E.ed.table_cells(ti):
                for cell in row:
                    out.extend(cell)
    return out


def top_paras():
    return [n for k, n, _t in E.ed.body_blocks() if k == "p"]


def ptext(p):
    return E.ed.para_text_of(p).replace("￼", "")


def text():
    """The body's text, paragraphs joined by newlines (tables left out)."""
    return "\n".join(ptext(p) for p in top_paras())


def para_texts():
    return [ptext(n) if k == "p" else "<table>" for k, n, _t in E.ed.body_blocks()]


def caret():
    return tuple(E.ed.caret_pos())


def pos():
    """The caret paragraph's text up to the caret."""
    p, o = caret()
    return ptext(p)[:o]


def caret_para_text():
    return ptext(caret()[0])


def sel():
    """The selected text, or None when nothing is selected."""
    if not E.ed.has_selection():
        return None
    return E.ed.selected_text()


def _order(a, b):
    order = {p: i for i, p in enumerate(all_paras())}
    ka, kb = (order.get(a[0], 0), a[1]), (order.get(b[0], 0), b[1])
    return (a, b) if ka <= kb else (b, a)


class Rng:
    """A stretch of the body from (node, offset) a to (node, offset) b."""

    def __init__(self, a, b=None):
        self.a, self.b = _order(tuple(a), tuple(b if b is not None else a))

    @property
    def start(self):
        return Rng(self.a)

    @property
    def end(self):
        return Rng(self.b)

    @property
    def text(self):
        (pa, oa), (pb, ob) = self.a, self.b
        ps = all_paras()
        if pa not in ps or pb not in ps:
            return ""
        i, j = ps.index(pa), ps.index(pb)
        if i == j:
            return ptext(pa)[oa:ob]
        return "\n".join([ptext(pa)[oa:]] + [ptext(p) for p in ps[i + 1:j]] + [ptext(pb)[:ob]])

    def select(self):
        E.ed.select_nodes(self.a[0], self.a[1], self.b[0], self.b[1])
        E.view.after_move()
        return self

    def caret_to_start(self):
        Rng(self.a).select()
        return self

    def caret_to_end(self):
        Rng(self.b).select()
        return self

    def run(self):
        """Run formatting of the range (selected for the read, selection restored)."""
        return self._with(E.ed.run_values)

    def para(self):
        return _named(self._with(E.ed.para_values))

    def _with(self, fn):
        keep = (E.ed.anchor_pos(), E.ed.caret_pos())
        E.ed.select_nodes(self.a[0], self.a[1], self.b[0], self.b[1])
        try:
            return fn()
        finally:
            E.ed.select_nodes(keep[0][0], keep[0][1], keep[1][0], keep[1][1])

    def __repr__(self):
        return "Rng(%r)" % self.text


def para_rng(i):
    """Top-level paragraph i as a range."""
    p = top_paras()[i]
    return Rng((p, 0), (p, len(ptext(p))))


def doc_rng():
    ps = top_paras()
    return Rng((all_paras()[0], 0), (ps[-1], len(ptext(ps[-1]))))


def sel_rng():
    pa, oa, pb, ob = E.ed.selection_range()
    return Rng((pa, oa), (pb, ob))


def find(word, nth=0, case=False, whole=False, regex=False):
    hits = find_all(word, case, whole, regex)
    return hits[nth] if nth < len(hits) else None


def find_all(word, case=False, whole=False, regex=False):
    try:
        hits = E.ed.find_all(word, {"match_case": case, "whole_word": whole, "regex": regex})
    except Exception as e:
        log("find_all(%r) failed: %s" % (word, e))
        return []
    return [Rng((h[0], h[1]), (h[2], h[3])) for h in hits]


def select(r):
    r.select()


def rv(i=None):
    """Run formatting at the caret (or of top-level paragraph i's text)."""
    return para_rng(i).run() if i is not None else E.ed.run_values()


def pv(i=None):
    """Paragraph formatting at the caret (or of top-level paragraph i)."""
    return para_rng(i).para() if i is not None else _named(E.ed.para_values())


def style_name(sid):
    """A style's name from its id (Heading1 -> Heading 1)."""
    for st in E.ed.style_list():
        if st[0] == sid:
            return st[1]
    return sid


def _named(d):
    """para_values with the style's name under 'style' (its id under 'style_id')."""
    d = dict(d)
    d["style_id"] = d.get("style")
    d["style"] = style_name(d.get("style"))
    return d


def style_of(i=None):
    return pv(i).get("style")


def list_info(i=None):
    """(list id, level, ..., label) of paragraph i (caret paragraph when None), or None."""
    try:
        return E.ed.list_info_of(top_paras()[i]) if i is not None else E.ed.list_info()
    except Exception:
        return None


def list_label(i=None):
    li = list_info(i)
    return li[3] if li else ""


def list_level(i=None):
    li = list_info(i)
    return li[1] if li else 0


def is_listed(i=None):
    return list_info(i) is not None


def border(side, i=None):
    """(style, width in 1/8 pt, space, colour) of a paragraph border, or None."""
    return (pv(i).get("borders") or {}).get(side)


def tables():
    """Each body table as its cells' texts: [[cell text, ...], ...] per table."""
    out = []
    for k, _n, ti in E.ed.body_blocks():
        if k == "t":
            out.append([["\n".join(ptext(p) for p in cell) for cell in row]
                        for row in E.ed.table_cells(ti)])
    return out


def table_paras(t=0):
    """Table t's cells as paragraph-node lists: [[[node, ...], ...], ...]."""
    tis = [ti for k, _n, ti in E.ed.body_blocks() if k == "t"]
    return E.ed.table_cells(tis[t])


def cell_name(r, c):
    s = ""
    c += 1
    while c:
        c, rem = divmod(c - 1, 26)
        s = chr(65 + rem) + s
    return "%s%d" % (s, r + 1)


def cell(name, t=0):
    """Text of a cell by its name ('B2') in table t."""
    import re
    m = re.match(r"([A-Z]+)(\d+)$", name)
    col = 0
    for ch in m.group(1):
        col = col * 26 + ord(ch) - 64
    return tables()[t][int(m.group(2)) - 1][col - 1]


def cell_rng(name, t=0):
    import re
    m = re.match(r"([A-Z]+)(\d+)$", name)
    col = 0
    for ch in m.group(1):
        col = col * 26 + ord(ch) - 64
    ps = table_paras(t)[int(m.group(2)) - 1][col - 1]
    return Rng((ps[0], 0), (ps[-1], len(ptext(ps[-1]))))


def in_table():
    p = caret()[0]
    for k, _n, ti in E.ed.body_blocks():
        if k == "t":
            for r, row in enumerate(E.ed.table_cells(ti)):
                for c, ps in enumerate(row):
                    if p in ps:
                        return cell_name(r, c)
    return None


def undo_titles():
    """Undo step names, newest first."""
    return list(reversed(E.ed.undo_names()))


def modified():
    return bool(E.ed.modified)


def notes(endnotes=False):
    return E.ed.note_count(endnotes)


def fields():
    """(depth, code, result) of every field in the body."""
    return list(E.ed.fields_all())


def tocs():
    return [r for _d, c, r in E.ed.fields_all() if c.strip().upper().startswith("TOC")]


def comment_texts():
    cm = getattr(win, "comments", None)
    cs = getattr(cm, "comments", None) or {}
    out = []
    for c in (cs.values() if isinstance(cs, dict) else cs):
        out.append(c.get("text") if isinstance(c, dict) else getattr(c, "text", ""))
    return out


def objects(kind=None):
    """(node, name, kind, ...) of the floating and inline objects."""
    return [o for o in E.ed.objects_list() if kind is None or o[2] == kind]


def changes():
    return list(E.ed.changes())


def page_setup(sec=0):
    """Section sec's page: width/height/top/bottom/left/right in twips, cols..."""
    return E.ed.page_setup(sec) or {}


def page_of_section(sec=0):
    for i in range(E.ed.page_count()):
        if E.ed.page_section(i) == sec:
            return i
    return 0


def header_on(sec=0):
    return bool(E.ed.page_hf(page_of_section(sec))[0])


def footer_on(sec=0):
    return bool(E.ed.page_hf(page_of_section(sec))[1])


def caret_page():
    return E.ed.caret_page()


def pages():
    return E.ed.page_count()


def link_here(r=None):
    if r is None:
        return E.ed.link_at_caret() or ""
    p, o = r.a
    mid = (r.a[1] + r.b[1]) // 2 if r.a[0] == r.b[0] else o + 1
    keep = (E.ed.anchor_pos(), E.ed.caret_pos())
    E.ed.select_nodes(p, mid, p, mid)
    try:
        return E.ed.link_at_caret() or ""
    finally:
        E.ed.select_nodes(keep[0][0], keep[0][1], keep[1][0], keep[1][1])


def type_at(r, s):
    """Replace range r with s (typing it), as an edit."""
    r.select()
    if s:
        E.ed.type_text(s)
    elif E.ed.has_selection():
        E.ed.delete(True, False)
    E.view.after_edit()


def set_text(s):
    """Replace the whole body with s (newlines make paragraphs)."""
    E.ed.select_all()
    E.ed.delete(True, False)
    for i, part in enumerate(s.split("\n")):
        if i:
            E.ed.type_text("\n")
        if part:
            E.ed.type_text(part)
    E.view.after_edit()


def caret_start():
    E.ed.move_caret("doc_start", False)
    E.view.after_move()


def caret_end():
    E.ed.move_caret("doc_end", False)
    E.view.after_move()


def object_info(node):
    """The object's page, x, y, w, h (points), rot, inline, kind, wrap (selects it)."""
    E.ed.select_object_node(node)
    d = E.ed.selected_object()
    return dict(d) if d else None


def insert_picture(path):
    ok = E.ed.insert_picture(path)
    E.view.after_edit()
    return ok


def comments():
    return [dict(c) for c in E.ed.comments()]


def docx_parts():
    """The document as it would be saved: {part name: text}."""
    import io, zipfile
    z = zipfile.ZipFile(io.BytesIO(bytes(E.ed.to_bytes())))
    return {n: z.read(n).decode("utf-8", "replace") for n in z.namelist() if n.endswith(".xml")}


def part_xml(name):
    return docx_parts().get(name, "")


def part_text(name):
    """The text (w:t contents) of a part of the document as saved, e.g. 'word/footnotes.xml'."""
    import re
    return "".join(re.findall(r"<w:t(?:\s[^>]*)?>([^<]*)</w:t>", part_xml(name)))


def parts_text(prefix):
    """The text of every part whose name starts with prefix ('word/header')."""
    import re
    out = []
    for n, x in sorted(docx_parts().items()):
        if n.startswith(prefix):
            t = "".join(re.findall(r"<w:t(?:\s[^>]*)?>([^<]*)</w:t>", x))
            if t:
                out.append(t)
    return out


def parts_xml(prefix):
    return "".join(x for n, x in sorted(docx_parts().items()) if n.startswith(prefix))


def drop_caps():
    """(paragraph text, drop cap info) of each paragraph with a drop cap."""
    keep = (E.ed.anchor_pos(), E.ed.caret_pos())
    out = []
    for p in top_paras():
        E.ed.select_nodes(p, 0, p, 0)
        info = E.ed.drop_cap_info()
        if info and info[0] not in ("", "none"):
            out.append((ptext(p), info))
    E.ed.select_nodes(keep[0][0], keep[0][1], keep[1][0], keep[1][1])
    return out


def cell_border(name, side, t=0):
    """Is the cell's own border on that side ('top', 'left'...) set (caret goes there)?"""
    cell_rng(name, t).caret_to_start()
    return E.ed.cell_border_on(side)
