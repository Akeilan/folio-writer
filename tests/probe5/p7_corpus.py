# Open every corpus file; compare page count and words against LibreOffice's rendering of the same file.
import os as _o; TESTS = _o.environ["FOLIO_WRITER_TESTS"]; exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read()); exec(open("/tmp/p5/probes/ph.py").read())
import subprocess, glob, collections, sys
C = "/tmp/corpus"
MSG = []
win.dialogs.message = lambda *a, **k: MSG.append(str(a[0])[:120] if a else "")
win.dialogs.confirm = lambda *a, **k: True
ERRS = []
sys.excepthook = lambda t, v, tb: ERRS.append("%s: %s" % (t.__name__, str(v)[:150]))
LOADED = {"n": 0, "ok": None}
_l = win._loaded
def _loaded(ok):
    LOADED["n"] += 1; LOADED["ok"] = ok
    return _l(ok)
win._loaded = _loaded
def words(pdf):
    t = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True).stdout
    return collections.Counter(w for w in re.findall(r"[^\W\d_]{3,}", t))
def pages(pdf):
    o = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout
    m = re.search(r"Pages:\s+(\d+)", o); return int(m.group(1)) if m else -1
import re
OUT = open("/tmp/p5out/p7_corpus.tsv", "w")
def a():
    yield 0.5
    files = sorted(glob.glob(C + "/*.docx")) + sorted(glob.glob(C + "/lo/*"))
    for f in files:
        base = os.path.basename(f).split(".")[0].replace("lo_", "")
        ref = "%s/ref/%s.pdf" % (C, base)
        del MSG[:]; del ERRS[:]; n0 = LOADED["n"]
        t0 = time.time()
        win.open_file(f)
        while LOADED["n"] == n0 and time.time() - t0 < 60:
            yield 0.1
        dt = time.time() - t0
        yield 0.6
        row = [os.path.basename(f), "%.1fs" % dt]
        if LOADED["n"] == n0 or not LOADED["ok"] or MSG:
            row += ["OPEN FAILED", ";".join(MSG)[:150], ";".join(ERRS)[:200]]
            OUT.write("\t".join(row) + "\n"); OUT.flush(); continue
        pdf = "/tmp/p5out/corpus_%s.pdf" % os.path.basename(f).replace(".", "_")
        try:
            win.engine.save_as(pdf, keep=False)
            pg, rp = pages(pdf), pages(ref)
            w, rw = words(pdf), words(ref)
            missing = sum((rw - w).values()); extra = sum((w - rw).values()); tot = max(1, sum(rw.values()))
            miss_ex = [k for k, _v in (rw - w).most_common(5)]
            row += ["pages %d vs %d%s" % (pg, rp, "" if pg == rp else "  DIFF"), "words missing %d/%d extra %d" % (missing, tot, extra), ",".join(miss_ex), ";".join(ERRS)[:200]]
            # save and reopen: does it survive its own save?
            p2 = "/tmp/p5out/corpus_resave.docx"
            ed().save(p2)
        except Exception as e:
            row += ["EXPORT FAILED", repr(e)[:200]]
        OUT.write("\t".join(row) + "\n"); OUT.flush()
    OUT.write("DONE\n"); OUT.close()
run_scenarios(a)
