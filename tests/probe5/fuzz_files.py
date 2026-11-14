# Damaged and odd files: the engine must open them or refuse cleanly. Never panic, never hang.
import sys, random, zipfile, io, os, time, signal
sys.path.insert(0, "/tmp/p5/app")
import folio_core as core
BASES = ["/tmp/corpus/styles.docx", "/tmp/corpus/tables.docx", "/tmp/corpus/lists.docx", "/tmp/corpus/sections.docx", "/tmp/corpus/pictures.docx", "/tmp/corpus/61745.docx", "/tmp/corpus/breaks.docx"]
N = int(sys.argv[1]) if len(sys.argv) > 1 else 300
class Hang(Exception): pass
def on_alarm(*a): raise Hang()
signal.signal(signal.SIGALRM, on_alarm)
def parts(path):
    with zipfile.ZipFile(path) as z:
        return [(i.filename, z.read(i.filename)) for i in z.infolist()]
def pack(ps):
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w", zipfile.ZIP_DEFLATED) as z:
        for n, d in ps: z.writestr(n, d)
    return b.getvalue()
def mutate(r, ps):
    ps = list(ps); how = r.choice(["drop_part", "truncate_xml", "flip_bytes", "dup_tag", "del_chunk", "empty_part", "huge_attr", "bad_rel", "truncate_zip", "garbage", "swap_tags", "num_overflow", "deep_nest"])
    xmls = [i for i, (n, _d) in enumerate(ps) if n.endswith(".xml") or n.endswith(".rels")]
    i = r.choice(xmls); n, d = ps[i]
    if how == "drop_part": del ps[i]
    elif how == "truncate_xml": ps[i] = (n, d[:r.randint(0, len(d))])
    elif how == "flip_bytes":
        b = bytearray(d)
        for _ in range(r.randint(1, 8)): b[r.randrange(len(b))] = r.randrange(256)
        ps[i] = (n, bytes(b))
    elif how == "dup_tag":
        a = r.randrange(len(d)); z = min(len(d), a + r.randint(10, 400)); ps[i] = (n, d[:z] + d[a:z] + d[z:])
    elif how == "del_chunk":
        a = r.randrange(len(d)); z = min(len(d), a + r.randint(1, 300)); ps[i] = (n, d[:a] + d[z:])
    elif how == "empty_part": ps[i] = (n, b"")
    elif how == "huge_attr":
        ps[i] = (n, d.replace(b'w:val="', b'w:val="' + b"9" * r.choice([20, 2000]), r.randint(1, 5)))
    elif how == "bad_rel":
        ps = [(m, (e.replace(b'Target="', b'Target="../../x/', 3) if m.endswith(".rels") else e)) for m, e in ps]
    elif how == "truncate_zip":
        raw = pack(ps); return how, raw[:r.randint(0, len(raw))]
    elif how == "garbage":
        return how, bytes(r.randrange(256) for _ in range(r.randint(0, 5000)))
    elif how == "swap_tags":
        ps[i] = (n, d.replace(b"<w:p>", b"<w:tbl>", r.randint(1, 3)).replace(b"</w:tc>", b"</w:p>", r.randint(0, 2)))
    elif how == "num_overflow":
        import re
        ps[i] = (n, re.sub(rb'="(\d+)"', lambda m: b'="' + r.choice([b"-1", b"0", b"99999999999999999999", b"2147483648", b"NaN", b"1e9"]) + b'"', d, count=r.randint(1, 30)))
    elif how == "deep_nest":
        ps[i] = (n, d.replace(b"<w:body>", b"<w:body>" + b"<w:tbl><w:tr><w:tc>" * 300, 1))
    return how, pack(ps)
res = {}
slow = []
for k in range(N):
    r = random.Random(k)
    base = r.choice(BASES)
    how, data = mutate(r, parts(base))
    t0 = time.time(); signal.alarm(20)
    try:
        e = core.Editor.from_bytes(data)
        e.page_count()
        e.select_all(); e.selected_text()
        p = "/tmp/p5out/ff_%d.docx" % os.getpid(); e.save(p)
        e.export_pdf(p + ".pdf")
        out = "opened"
    except Hang:
        out = "HANG >20s"
    except BaseException as ex:
        out = "PANIC: " + str(ex)[:140] if type(ex).__name__ == "PanicException" else "refused"
    signal.alarm(0)
    dt = time.time() - t0
    if dt > 5: slow.append((k, how, round(dt, 1)))
    res.setdefault((out if out.startswith(("PANIC", "HANG")) else out), []).append((k, how, os.path.basename(base)))
for k, v in sorted(res.items(), key=lambda kv: -len(kv[1])):
    print("%4d  %s   e.g. %s" % (len(v), k, v[:3]))
print("slow:", slow[:10])
