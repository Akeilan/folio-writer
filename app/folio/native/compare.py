"""Review > Compare and Combine: the original document opened with the
differences from the revised one made as tracked changes (insertions and
deletions, word by word inside changed paragraphs, cell by cell in tables of
the same shape), labelled with the reviewer's name."""
import difflib
import re

TOKEN = re.compile(r"\w+|\s+|[^\w\s]", re.UNICODE)


def _blocks(ed):
    """The body as a list of units: ("p", node, text) and ("t", index, cells),
    cells being the text of each cell's paragraphs."""
    out = []
    for kind, node, n in ed.body_blocks():
        if kind == "p":
            out.append(("p", node, ed.para_text_of(node)))
        else:
            cells = [[[(p, ed.para_text_of(p)) for p in cell] for cell in row] for row in ed.table_cells(n)]
            out.append(("t", n, cells))
    return out


def _key(b):
    if b[0] == "p":
        return ("p", b[2])
    return ("t", tuple(tuple(tuple(t for _p, t in cell) for cell in row) for row in b[2]))


class _Apply:
    def __init__(self, ed):
        self.ed = ed
        self.n = 0

    def select(self, pa, a, pb, b):
        return self.ed.select_nodes(pa, a, pb, b)

    def words(self, para, old, new):
        """Turn paragraph `para` (text `old`) into `new`, word by word, from
        the end so the offsets before stay right."""
        a, b = TOKEN.findall(old), TOKEN.findall(new)
        sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
        pos = [0]
        for t in a:
            pos.append(pos[-1] + len(t))
        for tag, i1, i2, j1, j2 in reversed(sm.get_opcodes()):
            if tag == "equal":
                continue
            ins = "".join(b[j1:j2])
            if i2 > i1:
                if not self.select(para, pos[i1], para, pos[i2]):
                    continue
                if ins:
                    self.ed.type_text(ins)
                else:
                    self.ed.delete(True)
            else:
                if not self.select(para, pos[i1], para, pos[i1]):
                    continue
                self.ed.type_text(ins)
            self.n += 1

    def delete_paras(self, units):
        """Delete whole paragraphs (and their marks)."""
        for u in reversed(units):
            if u[0] != "p":
                continue          # tables are left (a deleted table isn't marked)
            node, text = u[1], u[2]
            nxt = self._next_para(node)
            if nxt is not None:
                ok = self.select(node, 0, nxt, 0)
            else:
                ok = self.select(node, 0, node, len(text))
            if ok:
                self.ed.delete(True)
                self.n += 1

    def _next_para(self, node):
        blocks = self.ed.body_blocks()
        for i, (k, n, _x) in enumerate(blocks):
            if n == node:
                for k2, n2, _y in blocks[i + 1:]:
                    if k2 == "p":
                        return n2
                return None
        return None

    def insert_paras(self, after, before, texts):
        """New paragraphs after paragraph `after` (or before `before` at the
        start of the document)."""
        texts = [t for t in texts if t is not None]
        if not texts:
            return
        if after is not None:
            if not self.select(after[1], len(after[2]), after[1], len(after[2])):
                return
            self.ed.type_text("\n" + "\n".join(texts))
        elif before is not None:
            if not self.select(before[1], 0, before[1], 0):
                return
            self.ed.type_text("\n".join(texts) + "\n")
        self.n += 1


def compare(win, revised_path, author, combine=False):
    """Make the differences of `revised_path` from this window's document
    tracked changes by `author`. Returns how many changes were made, or None
    when the revised document can't be read."""
    import os
    from . import core
    try:
        if os.path.splitext(revised_path)[1].lower() in (".docx", ".docm", ".dotx", ".dotm"):
            other = core().Editor.open(revised_path)
        else:
            other = win.engine._import(revised_path)
    except Exception as e:
        print("compare:", e)
        return None
    ed = win.engine.ed
    a_units, b_units = _blocks(ed), _blocks(other)
    was_track = ed.track_changes()
    ed.set_markup("all")
    ed.set_author(author)
    ed.set_track_changes(True)
    ap = _Apply(ed)
    ed.begin_group("Combine Documents" if combine else "Compare Documents")
    try:
        sm = difflib.SequenceMatcher(None, [_key(u) for u in a_units], [_key(u) for u in b_units],
                                     autojunk=False)
        for tag, i1, i2, j1, j2 in reversed(sm.get_opcodes()):
            if tag == "equal":
                continue
            olds, news = a_units[i1:i2], b_units[j1:j2]
            if tag == "replace":
                # pair paragraphs (and tables of the same shape) one to one; the
                # rest are deleted or inserted
                k = 0
                pairs = []
                while k < min(len(olds), len(news)) and olds[k][0] == news[k][0]:
                    pairs.append((olds[k], news[k]))
                    k += 1
                extra_old, extra_new = olds[k:], news[k:]
                # inserted ones go after the last paired paragraph
                last = next((o for o, _n in reversed(pairs) if o[0] == "p"), None)
                if extra_new:
                    anchor = last or _prev_para(a_units, i1)
                    ap.insert_paras(anchor, None if anchor else _next_unit_para(a_units, i1),
                                    [u[2] for u in extra_new if u[0] == "p"])
                ap.delete_paras(extra_old)
                for o, n in reversed(pairs):
                    if o[0] == "p":
                        ap.words(o[1], o[2], n[2])
                    else:
                        _table(ap, o[2], n[2])
            elif tag == "delete":
                ap.delete_paras(olds)
            elif tag == "insert":
                anchor = _prev_para(a_units, i1)
                ap.insert_paras(anchor, None if anchor else _next_unit_para(a_units, i1),
                                [u[2] for u in news if u[0] == "p"])
    finally:
        ed.end_group()
        ed.set_track_changes(was_track)
    win.engine.view.document_changed()
    return ap.n


def _prev_para(units, i):
    for u in reversed(units[:i]):
        if u[0] == "p":
            return u
    return None


def _next_unit_para(units, i):
    for u in units[i:]:
        if u[0] == "p":
            return u
    return None


def _table(ap, old, new):
    """Tables of the same shape: cell by cell, paragraph by paragraph."""
    if len(old) != len(new) or any(len(r1) != len(r2) for r1, r2 in zip(old, new)):
        return
    for r1, r2 in reversed(list(zip(old, new))):
        for c1, c2 in reversed(list(zip(r1, r2))):
            for k in reversed(range(min(len(c1), len(c2)))):
                if c1[k][1] != c2[k][1]:
                    ap.words(c1[k][0], c1[k][1], c2[k][1])
            if len(c2) > len(c1) and c1:
                last = c1[-1]
                ap.insert_paras(("p", last[0], last[1]), None, [t for _p, t in c2[len(c1):]])
            elif len(c1) > len(c2):
                ap.delete_paras([("p", p, t) for p, t in c1[len(c2):]])
