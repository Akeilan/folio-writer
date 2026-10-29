import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
# 2.32 (W3-07): master documents — Outlining > Master Document
import os
import re
import shutil
import zipfile

from folio.native import masterdoc as M
from folio import masterui as MU

MSG = []
win.dialogs.message = lambda text, *a, **k: MSG.append(text)
D = "/tmp/n41"
shutil.rmtree(D, ignore_errors=True)
os.makedirs(D)


def body(ed):
    return [ed.para_text_of(n) for k, n, _t in ed.body_blocks() if k == "p"]


def a():
    yield 1.0
    A = win.actions
    ed = E.ed
    A.apply_style("Title"); ed.type_text("Book\n")
    A.apply_style("Heading 1"); ed.type_text("Chapter One\n")
    A.apply_style("Normal"); ed.type_text("First chapter text.\n")
    A.apply_style("Heading 1"); ed.type_text("Chapter Two\n")
    A.apply_style("Normal"); ed.type_text("Second chapter text.\nMore of chapter two.")
    E.view.after_edit(); yield 0.3
    master = D + "/Book.docx"
    check("master saved", win.save_to(master)); yield 0.5
    # ---- Outline view: the Master Document group
    win.act_outline_view(); yield 0.8
    v = win.outline()
    btns = win.master_buttons
    check("group shown", v is not None and set(btns) >= {"show", "collapse", "create", "insert", "unlink",
                                                         "merge", "split", "lock"}, sorted(btns))
    check("editing commands hidden until Show Document", not btns["create"].get_visible())
    MU.show_document(win); yield 0.2
    check("Show Document reveals them", btns["create"].get_visible() and btns["split"].get_visible())
    # ---- Create: each chapter heading becomes a subdocument
    paras = M._paras(ed)
    nodes = [p[0] for p in paras]
    texts = [p[1] for p in paras]
    i1, i2 = texts.index("Chapter One"), texts.index("Chapter Two")
    ed.select_nodes(nodes[i1], 0, nodes[i2], 3)
    MU.create(win); yield 0.3
    subs = M.subdocs(ed)
    check("two subdocuments created", len(subs) == 2 and all(e for _n, e, _p in subs), subs)
    rg = M.ranges(ed)
    check("each holds its chapter", sorted((a, b) for a, b, _e in rg.values()) == [(i1, i2 - 1), (i2, len(paras) - 1)], rg)
    check("outline marks them", any("▤" in r[1] for r in _rows(v)), [r[1] for r in _rows(v)][:6])
    # ---- Save: subdocuments in their own files, the master refers to them
    check("saved", win.save()); yield 1.0
    files = sorted(f for f in os.listdir(D) if f.endswith(".docx"))
    check("subdocument files", files == ["Book.docx", "Chapter One.docx", "Chapter Two.docx"], files)
    z = zipfile.ZipFile(master)
    doc = z.read("word/document.xml").decode()
    rels = z.read("word/_rels/document.xml.rels").decode()
    check("master has w:subDoc", doc.count("<w:subDoc ") == 2 and "Chapter One" not in doc, doc.count("<w:subDoc "))
    check("external subDocument relationships", rels.count("relationships/subDocument") == 2
          and "Chapter%20One.docx" in rels and 'TargetMode="External"' in rels, rels[-500:])
    sub = zipfile.ZipFile(D + "/Chapter One.docx").read("word/document.xml").decode()
    check("subdocument has its text and heading", "Chapter One" in sub and "First chapter text." in sub
          and "Chapter Two" not in sub and "Heading1" in sub)
    check("still shown expanded", "Second chapter text." in str(body(ed)))
    # ---- Collapse and Expand
    MU.collapse_expand(win); yield 0.5
    b = body(ed)
    check("collapsed to links", any(t.endswith("Chapter One.docx") for t in b) and "First chapter text." not in str(b), b)
    check("button says Expand", "Expand" in btns["collapse"].label, btns["collapse"].label)
    MU.collapse_expand(win); yield 0.5
    b = body(ed)
    check("expanded again", "First chapter text." in str(b) and "More of chapter two." in str(b), b)
    # ---- Split, Merge, Unlink
    paras = M._paras(ed)
    texts = [p[1] for p in paras]
    k = texts.index("More of chapter two.")
    ed.select_nodes(paras[k][0], 0, paras[k][0], 0)
    MU.split(win); yield 0.2
    check("split makes three", len(M.subdocs(ed)) == 3, M.subdocs(ed))
    paras = M._paras(ed)
    texts = [p[1] for p in paras]
    ed.select_nodes(paras[texts.index("Chapter Two")][0], 0, paras[texts.index("More of chapter two.")][0], 4)
    MU.merge(win); yield 0.2
    check("merge makes two again", len(M.subdocs(ed)) == 2, M.subdocs(ed))
    paras = M._paras(ed)
    texts = [p[1] for p in paras]
    ed.select_nodes(paras[texts.index("First chapter text.")][0], 0, paras[texts.index("First chapter text.")][0], 0)
    MU.unlink(win); yield 0.2
    check("unlink leaves one", len(M.subdocs(ed)) == 1 and "First chapter text." in str(body(ed)), M.subdocs(ed))
    # ---- reopen: Word shows a master's subdocuments collapsed
    check("saved again", win.save()); yield 1.0
    ed.mark_saved()
    win.open_file(master); yield 2.0
    b = body(E.ed)
    check("reopened collapsed", any(t.endswith("Chapter Two.docx") for t in b) and "First chapter text." in str(b), b)
    check("subdocument known", len(M.subdocs(E.ed)) == 1 and not M.subdocs(E.ed)[0][1], M.subdocs(E.ed))
    check("not marked changed", not E.ed.modified)
    win.act_outline_view(); yield 0.5
    MU.collapse_expand(win); yield 0.5
    check("expands from its file", "Second chapter text." in str(body(E.ed)), body(E.ed))
    # ---- Insert a document as a subdocument
    other = D + "/Appendix.docx"
    from folio.native import docxbuild as B
    d = B.Doc()
    s = B.section()
    s["blocks"] = [B.para("Appendix", style="Heading1"), B.para("Appendix text.")]
    d.sections = [s]
    with open(other, "wb") as fh:
        fh.write(B.to_docx(d))
    paras = M._paras(E.ed)
    E.ed.select_nodes(paras[-1][0], len(paras[-1][1]), paras[-1][0], len(paras[-1][1]))
    win.dialogs.pick_file = lambda *a, **k: other
    MU.insert(win); yield 0.5
    check("inserted subdocument", len(M.subdocs(E.ed)) == 2 and "Appendix text." in str(body(E.ed)), M.subdocs(E.ed))
    check("it keeps its file", any(p.endswith("Appendix.docx") for _n, _e, p in M.subdocs(E.ed)), M.subdocs(E.ed))
    # ---- Lock Document
    MU.lock(win); yield 0.2
    check("locked read-only", win.read_only and "Read-Only" in win.get_title(), win.get_title())
    MU.lock(win); yield 0.2
    check("unlocked", not win.read_only)
    E.ed.mark_saved()
    win.act_close_outline(); yield 0.3


def _rows(v):
    out = []

    def walk(it):
        while it is not None:
            out.append(tuple(v.store[it])[:3])
            walk(v.store.iter_children(it))
            it = v.store.iter_next(it)
    walk(v.store.get_iter_first())
    return out


run_scenarios(a)
