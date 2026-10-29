"""Master documents (W3-07): Outlining > Master Document, as in Word.

Show Document, Collapse/Expand Subdocuments, Create, Insert, Unlink, Merge, Split and Lock
Document. A subdocument is a part of the master kept in a file of its own:

* in the editor, an expanded subdocument is the text between the bookmark "_SubDoc<n>"'s
  ends; a collapsed one is a paragraph with a link to its file, marked "_SubDocLink<n>";
  the document variable "FolioSubDoc<n>" names the file;
* in the saved .docx, as Word writes it, each is a <w:subDoc r:id/> in the body whose
  relationship (subDocument, external) points at the file. Saving writes every expanded
  subdocument to its file; opening shows them collapsed, as Word does."""
import os
import re
import shutil
import tempfile
import urllib.parse
import zipfile
from xml.dom import minidom
from xml.sax.saxutils import escape, quoteattr

REL_SUBDOC = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/subDocument"
REL_LINK = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink"
EXPANDED = re.compile(r"^_SubDoc(\d+)$")
COLLAPSED = re.compile(r"^_SubDocLink(\d+)$")
BODY = 10


# ------------------------------------------------------------------ document variables
def _docvar(ed, name):
    x = ed.settings_xml("w:docVars") or ""
    m = re.search(r'<w:docVar w:name=%s w:val="([^"]*)"' % re.escape(quoteattr(name)), x)
    if not m:
        return ""
    from xml.sax.saxutils import unescape
    return unescape(m.group(1), {"&quot;": '"'})


def _set_docvar(ed, name, value):
    x = ed.settings_xml("w:docVars") or ""
    if not x or x.rstrip().endswith("/>") and "<w:docVar " not in x:
        x = "<w:docVars></w:docVars>"
    x = re.sub(r'<w:docVar w:name=%s w:val="[^"]*"\s*/>' % re.escape(quoteattr(name)), "", x)
    if value:
        x = x.replace("</w:docVars>", "<w:docVar w:name=%s w:val=%s/></w:docVars>" % (quoteattr(name), quoteattr(value)))
    ed.set_settings_xml("w:docVars", x if "<w:docVar " in x else None)


# ------------------------------------------------------------------ the subdocuments
def subdocs(ed):
    """[(n, expanded, path)] in number order."""
    out = []
    for name in ed.all_bookmark_names():
        m = EXPANDED.match(name) or COLLAPSED.match(name)
        if m:
            n = int(m.group(1))
            out.append((n, bool(EXPANDED.match(name)), _docvar(ed, "FolioSubDoc%d" % n)))
    return sorted(out)


def is_master(ed):
    return bool(subdocs(ed))


def _next(ed):
    return max([n for n, _e, _p in subdocs(ed)] + [0]) + 1


def _paras(ed):
    """The body's paragraphs: [(node, text, level)]."""
    return [(r[0], r[1], r[2]) for r in ed.outline_paras()]


def _range(ed, name):
    """(index of first paragraph, index of last) a bookmark covers, in _paras order."""
    keep = (ed.anchor_pos(), ed.caret_pos())
    try:
        if not ed.select_bookmark(name):
            return None
        a, _ao, b, _bo = ed.selection_range()
    finally:
        ed.select_nodes(keep[0][0], keep[0][1], keep[1][0], keep[1][1])
    nodes = [p[0] for p in _paras(ed)]
    if a not in nodes or b not in nodes:
        return None
    ia, ib = nodes.index(a), nodes.index(b)
    return (min(ia, ib), max(ia, ib))


def ranges(ed):
    """{n: (first, last, expanded)}."""
    out = {}
    for n, exp, _p in subdocs(ed):
        r = _range(ed, ("_SubDoc%d" if exp else "_SubDocLink%d") % n)
        if r:
            out[n] = (r[0], r[1], exp)
    return out


def _paste_marked(ed, xml, name):
    """Paste a document's body at the caret (an empty paragraph) and mark what came in
    with the bookmark `name`. Paragraph positions, not nodes, track it: pasting may
    replace the paragraph the caret was in."""
    nodes = [p[0] for p in _paras(ed)]
    node = ed.caret_pos()[0]
    if node not in nodes:
        return False
    i0 = nodes.index(node)
    ed.paste_fragment(xml, False)
    paras = _paras(ed)
    nodes = [p[0] for p in paras]
    cn, coff = ed.caret_pos()
    if cn not in nodes:
        return False
    j = nodes.index(cn)
    if coff == 0 and not paras[j][1] and j > i0:
        # the empty paragraph left after the pasted ones is not part of it
        ed.select_nodes(paras[j - 1][0], len(paras[j - 1][1]), cn, 0)
        ed.delete(True, False)
        paras = _paras(ed)
        j -= 1
    _select_paras(ed, paras, i0, j)
    ok = ed.add_bookmark(name)
    ed.select_nodes(paras[i0][0], 0, paras[i0][0], 0)
    return ok


def _select_paras(ed, paras, i, j):
    return ed.select_nodes(paras[i][0], 0, paras[j][0], len(paras[j][1]))


def at_caret(ed):
    """The subdocument the caret is in: n or None."""
    node = ed.caret_pos()[0]
    nodes = [p[0] for p in _paras(ed)]
    if node not in nodes:
        return None
    i = nodes.index(node)
    for n, (a, b, _e) in ranges(ed).items():
        if a <= i <= b:
            return n
    return None


# ------------------------------------------------------------------ commands
def create(ed, start_node=None):
    """Create: the selected heading (with what it heads) becomes a subdocument; with
    several headings selected, one for each heading at the level of the first."""
    paras = _paras(ed)
    nodes = [p[0] for p in paras]
    a, _ao, b, _bo = ed.selection_range()
    if start_node is not None:
        a = b = start_node
    if a not in nodes or b not in nodes:
        return 0
    ia, ib = sorted((nodes.index(a), nodes.index(b)))
    taken = ranges(ed)
    heads = [i for i in range(ia, ib + 1) if paras[i][2] != BODY]
    if not heads:
        spans = [(ia, ib)]
    else:
        level = paras[heads[0]][2]
        starts = [i for i in heads if paras[i][2] == level]
        spans = []
        for k, s in enumerate(starts):
            e = s
            limit = starts[k + 1] - 1 if k + 1 < len(starts) else len(paras) - 1
            while e + 1 <= limit and (paras[e + 1][2] == BODY or paras[e + 1][2] > level):
                e += 1
            if k + 1 == len(starts) and ib > s and len(starts) > 1:
                e = max(e, min(ib, limit))
            spans.append((s, e))
    made = 0
    for s, e in spans:
        if any(not (e < x or s > y) for x, y, _ex in taken.values()):
            continue                         # already part of a subdocument
        n = _next(ed)
        _select_paras(ed, paras, s, e)
        if ed.add_bookmark("_SubDoc%d" % n):
            _set_docvar(ed, "FolioSubDoc%d" % n, "")
            made += 1
    if paras:
        ed.select_nodes(paras[spans[0][0]][0], 0, paras[spans[0][0]][0], 0)
    return made


def insert(ed, path, master_path=None):
    """Insert: a document becomes a subdocument at the caret (shown expanded)."""
    from . import insertfile
    node, off = ed.caret_pos()
    if ed.para_text_of(node):
        ed.select_nodes(node, len(ed.para_text_of(node)), node, len(ed.para_text_of(node)))
        ed.type_text("\n")
    xml = insertfile._docx_body(path)
    if not xml:
        return None
    n = _next(ed)
    if not _paste_marked(ed, xml, "_SubDoc%d" % n):
        return None
    _set_docvar(ed, "FolioSubDoc%d" % n, _stored_path(path, master_path))
    return n


def unlink(ed, n=None):
    """Unlink: the subdocument's text becomes part of the master."""
    n = at_caret(ed) if n is None else n
    if n is None:
        return False
    exp = any(k == n and e for k, e, _p in subdocs(ed))
    if not exp:
        return False                         # Word unlinks expanded subdocuments only
    ed.delete_bookmark("_SubDoc%d" % n)
    _set_docvar(ed, "FolioSubDoc%d" % n, "")
    return True


def merge(ed):
    """Merge: the selected subdocuments become one (the first one's file)."""
    paras = _paras(ed)
    nodes = [p[0] for p in paras]
    a, _ao, b, _bo = ed.selection_range()
    if a not in nodes or b not in nodes:
        return False
    ia, ib = sorted((nodes.index(a), nodes.index(b)))
    picked = sorted((x, y, n) for n, (x, y, e) in ranges(ed).items() if e and not (y < ia or x > ib))
    if len(picked) < 2:
        return False
    first = picked[0][2]
    lo, hi = picked[0][0], picked[-1][1]
    for _x, _y, n in picked:
        ed.delete_bookmark("_SubDoc%d" % n)
        if n != first:
            _set_docvar(ed, "FolioSubDoc%d" % n, "")
    _select_paras(ed, paras, lo, hi)
    ed.add_bookmark("_SubDoc%d" % first)
    ed.select_nodes(paras[lo][0], 0, paras[lo][0], 0)
    return True


def split(ed):
    """Split: the subdocument divides at the caret's paragraph (a new file for the rest)."""
    n = at_caret(ed)
    if n is None:
        return False
    paras = _paras(ed)
    nodes = [p[0] for p in paras]
    i = nodes.index(ed.caret_pos()[0])
    a, b, exp = ranges(ed)[n]
    if not exp or i <= a:
        return False
    ed.delete_bookmark("_SubDoc%d" % n)
    _select_paras(ed, paras, a, i - 1)
    ed.add_bookmark("_SubDoc%d" % n)
    m = _next(ed)
    _select_paras(ed, paras, i, b)
    ed.add_bookmark("_SubDoc%d" % m)
    _set_docvar(ed, "FolioSubDoc%d" % m, "")
    ed.select_nodes(paras[i][0], 0, paras[i][0], 0)
    return True


def collapse(ed, master_path):
    """Collapse Subdocuments: each is saved to its file and shown as a link to it."""
    done = 0
    for n, exp, _p in subdocs(ed):
        if not exp:
            continue
        path = write_subdoc(ed, n, master_path)
        if not path:
            continue
        ed.select_bookmark("_SubDoc%d" % n)
        ed.delete_bookmark("_SubDoc%d" % n)
        ed.delete(True, False)
        node = ed.caret_pos()[0]
        shown = _resolve(_docvar(ed, "FolioSubDoc%d" % n), master_path)
        ed.insert_hyperlink(_file_url(shown), shown)
        ed.select_nodes(node, 0, node, len(ed.para_text_of(node)))
        ed.add_bookmark("_SubDocLink%d" % n)
        done += 1
    return done


def expand(ed, master_path):
    """Expand Subdocuments: each link is replaced by its file's text again."""
    from . import insertfile
    done = 0
    for n, exp, rel in subdocs(ed):
        if exp:
            continue
        path = _resolve(rel, master_path)
        if not path or not os.path.exists(path):
            continue
        xml = insertfile._docx_body(path)
        if not xml:
            continue
        ed.select_bookmark("_SubDocLink%d" % n)
        ed.delete_bookmark("_SubDocLink%d" % n)
        node = ed.caret_pos()[0]
        ed.select_nodes(node, 0, node, len(ed.para_text_of(node)))
        ed.delete(True, False)
        _paste_marked(ed, xml, "_SubDoc%d" % n)
        done += 1
    return done


# ------------------------------------------------------------------ files
def _stored_path(path, master_path):
    """A subdocument's file as the master records it: relative to the master's folder."""
    if master_path:
        try:
            return os.path.relpath(path, os.path.dirname(os.path.abspath(master_path)))
        except ValueError:
            pass
    return os.path.abspath(path)


def _resolve(stored, master_path):
    if not stored:
        return ""
    p = urllib.parse.unquote(stored)
    if p.startswith("file://"):
        p = urllib.parse.urlparse(p).path
    if not os.path.isabs(p) and master_path:
        p = os.path.join(os.path.dirname(os.path.abspath(master_path)), p)
    return os.path.normpath(p)


def _file_url(path):
    return "file://" + urllib.parse.quote(os.path.abspath(path))


def _new_name(ed, n, master_path):
    """Word names a new subdocument's file after its first words."""
    paras = _paras(ed)
    r = _range(ed, "_SubDoc%d" % n)
    words = paras[r[0]][1] if r else ""
    base = re.sub(r"[^\w\- ]+", "", words).strip()[:40].strip() or "Subdocument %d" % n
    folder = os.path.dirname(os.path.abspath(master_path))
    name = base + ".docx"
    k = 1
    while os.path.exists(os.path.join(folder, name)):
        k += 1
        name = "%s%d.docx" % (base, k)
    return os.path.join(folder, name)


def write_subdoc(ed, n, master_path):
    """The expanded subdocument saved to its own file (with the master's styles)."""
    if not master_path:
        return None
    stored = _docvar(ed, "FolioSubDoc%d" % n)
    path = _resolve(stored, master_path) if stored else _new_name(ed, n, master_path)
    keep = (ed.anchor_pos(), ed.caret_pos())
    try:
        if not ed.select_bookmark("_SubDoc%d" % n):
            return None
        frag = ed.copy_fragment()
    finally:
        ed.select_nodes(keep[0][0], keep[0][1], keep[1][0], keep[1][1])
    if not frag:
        return None
    from . import core
    tmpd = tempfile.mkdtemp(prefix="folio-master-")
    try:
        base = os.path.join(tmpd, "master.docx")
        ed.save(base)
        other = core().Editor.open(base)
        from .mailmerge import clear
        clear(other)
        other.paste_fragment(frag, True)
        for name in other.all_bookmark_names():
            if EXPANDED.match(name) or COLLAPSED.match(name):
                other.delete_bookmark(name)
        other.set_settings_xml("w:docVars", None)
        tmp = path + ".folio-tmp"
        other.save(tmp)
        os.replace(tmp, path)
    finally:
        shutil.rmtree(tmpd, ignore_errors=True)
    if not stored:
        _set_docvar(ed, "FolioSubDoc%d" % n, _stored_path(path, master_path))
    return path


def before_save(ed, master_path):
    """Every expanded subdocument written to its file before the master is saved."""
    out = []
    for n, exp, _p in subdocs(ed):
        if exp:
            p = write_subdoc(ed, n, master_path)
            if p:
                out.append(p)
    return out


def after_save(path):
    """The saved master as Word writes it: each subdocument a <w:subDoc> in the body."""
    try:
        z = zipfile.ZipFile(path)
    except (OSError, zipfile.BadZipFile):
        return 0
    with z:
        parts = {n: z.read(n) for n in z.namelist()}
    doc = parts.get("word/document.xml", b"")
    if b"_SubDoc" not in doc:
        return 0
    settings = parts.get("word/settings.xml", b"").decode("utf-8", "replace")
    paths = {int(m.group(1)): m.group(2) for m in re.finditer(
        r'<w:docVar w:name="FolioSubDoc(\d+)" w:val="([^"]*)"', settings)}
    dom = minidom.parseString(doc)
    body = dom.getElementsByTagName("w:body")[0]
    kids = [k for k in body.childNodes if k.nodeType == k.ELEMENT_NODE]

    def top(node):
        while node is not None and node.parentNode is not body:
            node = node.parentNode
        return node
    ends = {e.getAttribute("w:id"): e for e in dom.getElementsByTagName("w:bookmarkEnd")}
    rels_add = []
    count = 0
    for bs in list(dom.getElementsByTagName("w:bookmarkStart")):
        m = EXPANDED.match(bs.getAttribute("w:name")) or COLLAPSED.match(bs.getAttribute("w:name"))
        if not m:
            continue
        n = int(m.group(1))
        target = paths.get(n)
        be = ends.get(bs.getAttribute("w:id"))
        a, b = top(bs), top(be) if be is not None else top(bs)
        if not target or a is None or b is None:
            continue
        kids = [k for k in body.childNodes if k.nodeType == k.ELEMENT_NODE]
        ia, ib = kids.index(a), kids.index(b)
        rid = "rIdSubDoc%d" % n
        sd = dom.createElement("w:subDoc")
        sd.setAttribute("r:id", rid)
        body.insertBefore(sd, kids[ia])
        for k in kids[ia:ib + 1]:
            body.removeChild(k)
        rels_add.append('<Relationship Id="%s" Type="%s" Target=%s TargetMode="External"/>'
                        % (rid, REL_SUBDOC, quoteattr(urllib.parse.quote(target.replace(os.sep, "/")))))
        count += 1
    if not count:
        return 0
    root = dom.documentElement
    if not root.getAttribute("xmlns:r"):
        root.setAttribute("xmlns:r", "http://schemas.openxmlformats.org/officeDocument/2006/relationships")
    parts["word/document.xml"] = dom.toxml(encoding="UTF-8")
    rp = "word/_rels/document.xml.rels"
    rels = parts.get(rp, b"").decode("utf-8")
    rels = re.sub(r'<Relationship Id="rIdSubDoc\d+"[^>]*/>', "", rels)
    parts[rp] = rels.replace("</Relationships>", "".join(rels_add) + "</Relationships>").encode("utf-8")
    _rezip(path, parts)
    return count


def _rezip(path, parts):
    tmp = path + ".folio-tmp"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as out:
        out.writestr("[Content_Types].xml", parts.pop("[Content_Types].xml"))
        for n, v in parts.items():
            out.writestr(n, v)
    os.replace(tmp, path)


def has_subdocs(path):
    try:
        with zipfile.ZipFile(path) as z:
            return b"<w:subDoc " in z.read("word/document.xml")
    except (OSError, KeyError, zipfile.BadZipFile):
        return False


def prepare(path, out_path):
    """A master .docx made ready to open: each <w:subDoc> shown collapsed, as a link.
    Returns [(n, file)] for opened(), which records them in the document."""
    with zipfile.ZipFile(path) as z:
        parts = {n: z.read(n) for n in z.namelist()}
    rp = "word/_rels/document.xml.rels"
    rels = parts.get(rp, b"").decode("utf-8")
    targets = {}
    for m in re.finditer(r"<Relationship\b[^>]*/>", rels):
        r = m.group(0)
        if REL_SUBDOC in r:
            rid = re.search(r'Id="([^"]+)"', r).group(1)
            targets[rid] = urllib.parse.unquote(re.search(r'Target="([^"]+)"', r).group(1))
    doc = parts["word/document.xml"].decode("utf-8")
    n = [0]
    links = []
    vars_ = []

    def link(m):
        rid = m.group(1)
        target = targets.get(rid)
        if target is None:
            return ""
        n[0] += 1
        k = n[0]
        shown = _resolve(target, path)
        lid = "rIdSubDocLink%d" % k
        links.append('<Relationship Id="%s" Type="%s" Target=%s TargetMode="External"/>'
                     % (lid, REL_LINK, quoteattr(_file_url(shown))))
        vars_.append((k, target))
        bid = str(90000 + k)
        return ('<w:p><w:bookmarkStart w:id="%s" w:name="_SubDocLink%d"/><w:hyperlink r:id="%s"><w:r><w:rPr>'
                '<w:color w:val="0563C1"/><w:u w:val="single"/></w:rPr><w:t xml:space="preserve">%s</w:t></w:r>'
                '</w:hyperlink><w:bookmarkEnd w:id="%s"/></w:p>' % (bid, k, lid, escape(shown), bid))
    doc = re.sub(r'<w:subDoc\s+r:id="([^"]+)"\s*/>', link, doc)
    parts["word/document.xml"] = doc.encode("utf-8")
    rels = re.sub(r"<Relationship\b[^>]*%s[^>]*/>" % re.escape(REL_SUBDOC), "", rels)
    parts[rp] = rels.replace("</Relationships>", "".join(links) + "</Relationships>").encode("utf-8")
    _rezip(out_path, parts)
    return vars_


def opened(ed, found):
    """After a master opens: which file each collapsed subdocument stands for."""
    for n, target in found:
        _set_docvar(ed, "FolioSubDoc%d" % n, target)
    ed.mark_saved()
