# Headless: random editing against the engine. No panics, saves that reopen, undo back to the start.
import sys, random, zipfile, io, traceback, time, os, re
sys.path.insert(0, "/tmp/p5/app")
import folio_core as core
import xml.dom.minidom as md
SEED0 = int(sys.argv[1]) if len(sys.argv) > 1 else 1
RUNS = int(sys.argv[2]) if len(sys.argv) > 2 else 40
STEPS = int(sys.argv[3]) if len(sys.argv) > 3 else 300
STRICT = len(sys.argv) > 4
BASES = ["/tmp/p5/share/templates/Normal-Letter.docx", "/tmp/corpus/styles.docx", "/tmp/corpus/tables.docx", "/tmp/corpus/lists.docx", "/tmp/corpus/sections.docx", "/tmp/corpus/pictures.docx"]
WORDS = "alpha beta gamma delta the quick brown fox jumps over a lazy dog 12 3.5 naïve façade".split()
MOVES = ["left", "right", "word_left", "word_right", "up", "down", "home", "end", "doc_start", "doc_end", "para_up", "para_down"]
TCMD = ["insert_rows_above", "insert_rows_below", "insert_cols_left", "insert_cols_right", "delete_rows", "delete_cols", "delete_table", "merge"]
def text_of(e):
    e.select_all(); t = e.selected_text(); e.move_caret("doc_start", False); return t
def body_text(e):
    b = io.BytesIO(); p = "/tmp/p5out/fz_%d.docx" % os.getpid(); e.save(p)
    with zipfile.ZipFile(p) as z:
        for n in z.namelist():
            if n.endswith(".xml") or n.endswith(".rels"):
                md.parseString(z.read(n))       # well-formed
        x = z.read("word/document.xml").decode("utf8")
    if STRICT: return p, x
    return p, re.sub(r"<[^>]+>", "", re.sub(r"</w:p>", "\n", x))
def ops(r):
    return [
        (30, lambda e: e.type_text(" ".join(r.choice(WORDS) for _ in range(r.randint(1, 6))) + r.choice(["", " ", ". "]))),
        (8, lambda e: e.type_text("\n")),
        (2, lambda e: e.type_text("\t")),
        (14, lambda e: e.move_caret(r.choice(MOVES), r.random() < 0.3)),
        (8, lambda e: e.delete(r.random() < 0.5, r.random() < 0.3)),
        (3, lambda e: e.toggle(r.choice(["w:b", "w:i", "w:strike", "w:caps"]))),
        (2, lambda e: e.set_align(r.choice(["left", "center", "right", "both"]))),
        (2, lambda e: e.set_style(r.choice(["Heading1", "Heading2", "Normal", "Title"]))),
        (3, lambda e: e.toggle_list(r.choice(["bullet", "number"]))),
        (2, lambda e: e.change_list_level(r.choice([-1, 1]))),
        (1, lambda e: e.set_size(float(r.choice([8, 11, 14, 28, 72])))),
        (1, lambda e: e.set_color(r.choice(["FF0000", "auto", "0000FF"]))),
        (1, lambda e: e.set_highlight(r.choice(["yellow", "none", "green"]))),
        (2, lambda e: e.insert_table(r.randint(1, 4), r.randint(1, 5))),
        (4, lambda e: e.cell_step(r.random() < 0.3)),
        (4, lambda e: e.table_command(r.choice(TCMD))),
        (1, lambda e: e.select_table_part(r.choice(["cell", "row", "column", "table"]))),
        (1, lambda e: e.split_cells(r.randint(1, 3), r.randint(1, 2))),
        (1, lambda e: e.select_all()),
        (2, lambda e: (e.insert_note(r.random() < 0.3), e.type_text("note " + r.choice(WORDS)), e.edit_notes(None))),
        (1, lambda e: (e.edit_header_footer(0, r.random() < 0.5), e.type_text("hf " + r.choice(WORDS)), e.edit_header_footer(None, False))),
        (1, lambda e: e.insert_field_now(r.choice(["PAGE", "NUMPAGES", "DATE"]))),
        (1, lambda e: e.insert_hyperlink("https://example.org/", "link")),
        (1, lambda e: e.insert_comment("remark", "Fuzz")),
        (1, lambda e: e.set_track_changes(r.random() < 0.5)),
        (1, lambda e: e.insert_toc(None)),
        (1, lambda e: e.add_bookmark("b%d" % r.randint(0, 5))),
        (1, lambda e: e.set_line_spacing("auto", r.choice([240, 360, 480]))),
        (1, lambda e: e.set_indent(r.choice([0, 720, 1440]), None, r.choice([None, 360, -360]))),
        (1, lambda e: e.clear_formatting()),
        (1, lambda e: e.move_block(r.random() < 0.5)),
        (6, lambda e: e.undo()),
        (3, lambda e: e.redo()),
        (2, lambda e: e.page_count()),
    ]
def pick(r, table):
    tot = sum(w for w, _f in table); x = r.uniform(0, tot)
    for w, f in table:
        x -= w
        if x <= 0: return f
    return table[-1][1]
fails = {}
def fail(kind, seed, step, detail):
    k = kind + " :: " + detail.strip().splitlines()[-1][:160]
    fails.setdefault(k, []).append((seed, step))
t0 = time.time(); total = 0
for seed in range(SEED0, SEED0 + RUNS):
    r = random.Random(seed)
    base = BASES[seed % len(BASES)]
    try:
        e = core.Editor.open(base)
    except BaseException as ex:
        fail("open", seed, 0, repr(ex)); continue
    table = ops(r)
    start = body_text(e)[1]
    alive = True
    for step in range(STEPS):
        f = pick(r, table)
        try:
            f(e); total += 1
        except BaseException as ex:
            name = type(ex).__name__
            if name == "PanicException":
                fail("PANIC", seed, step, str(ex)); alive = False; break
            # ordinary refusals (ValueError etc.) are allowed; record the kinds once
            fails.setdefault("refusal :: %s: %s" % (name, str(ex)[:100]), []).append((seed, step))
        if step % 40 == 39:
            try:
                p, t = body_text(e)
                e2 = core.Editor.open(p)
                p2, t2 = body_text(e2)
                if t != t2:
                    fail("REOPEN TEXT DIFFERS", seed, step, "len %d vs %d" % (len(t), len(t2)))
                if e2.page_count() != e.page_count():
                    fail("REOPEN PAGE COUNT DIFFERS", seed, step, "%d vs %d" % (e.page_count(), e2.page_count()))
            except BaseException as ex:
                fail("SAVE/REOPEN " + type(ex).__name__, seed, step, str(ex)); 
                if type(ex).__name__ == "PanicException": alive = False; break
    if not alive: continue
    try:
        e.edit_notes(None)
    except BaseException:
        pass
    try:
        n = 0
        while e.can_undo() and n < 5000:
            e.undo(); n += 1
        end = body_text(e)[1]
        if end != start:
            import difflib
            a_, b_ = start.replace("><", ">\n<").split("\n"), end.replace("><", ">\n<").split("\n")
            d = [l for l in difflib.unified_diff(a_, b_, lineterm="", n=0) if l[:1] in "+-" and l[:3] not in ("+++", "---")]
            fail("UNDO ALL != START", seed, n, "diff: " + " ".join(d)[:150])
    except BaseException as ex:
        fail("UNDO " + type(ex).__name__, seed, 0, str(ex))
print("last doc chars", len(start), len(end)); print("runs %d, ops %d, %.0fs" % (RUNS, total, time.time() - t0))
for k, v in sorted(fails.items(), key=lambda kv: (kv[0].startswith("refusal"), -len(kv[1]))):
    print("%4d  %s   e.g. seed/step %s" % (len(v), k, v[:3]))
