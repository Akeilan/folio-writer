import os as _o; TESTS = _o.environ["FOLIO_WRITER_TESTS"]; exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read()); exec(open("/tmp/p5/probes/ph.py").read())
import stat, subprocess
MSG = []; ERRS = []
import sys
sys.excepthook = lambda t, v, tb: ERRS.append("%s: %s" % (t.__name__, str(v)[:150]))
win.dialogs.message = lambda *a, **k: MSG.append(str(a[0])[:140] if a else "")
win.dialogs.confirm = lambda *a, **k: True
D = "/tmp/p5out/files"; subprocess.run(["rm", "-rf", D]); os.makedirs(D)
def opened(f, wait=1.5):
    del MSG[:]; del ERRS[:]
    win.open_file(f)
def a():
    yield 0.5
    focus(); fresh(); T("Some words to save."); yield 0.3
    # --- saving where it cannot
    del MSG[:]
    ok = win.save_to("/proc/nope/x.docx"); yield 0.3
    check("saving to a folder that doesn't exist fails and says so", (not ok) and MSG, (ok, MSG))
    check("and the document is still marked unsaved", ed().modified)
    os.makedirs(D + "/ro"); os.chmod(D + "/ro", 0o555)
    del MSG[:]
    ok = win.save_to(D + "/ro/x.docx"); yield 0.3
    note("read-only folder (running as root, so this may succeed)", (ok, MSG))
    # --- names
    for name in ("with spaces and ünïcödé ✓.docx", "x" * 200 + ".docx", "dots.in.name.v2.docx", "UPPER.DOCX", "noext"):
        del MSG[:]; del ERRS[:]
        p = D + "/" + name
        ok = win.save_to(p); yield 0.4
        check("save as %r" % name[:30], ok and os.path.exists(p) and not ERRS, (ok, MSG, ERRS, os.listdir(D)[-3:]))
        if ok:
            opened(p); yield 1.2
            check("and open it again %r" % name[:30], not MSG and "Some words to save." in body_text(), (MSG, body_text()[:40]))
    # --- things that are not documents
    open(D + "/zero.docx", "w").close()
    open(D + "/text.docx", "w").write("just text, not a zip\n")
    open(D + "/plain.txt", "w").write("Line one\nLine two\n\nLine four with a tab\there\n")
    open(D + "/latin1.txt", "wb").write("caf\xe9 na\xefve\n".encode("latin-1"))
    open(D + "/utf16.txt", "wb").write("UTF sixteen ✓\n".encode("utf-16"))
    open(D + "/big.txt", "w").write(("word " * 12 + "\n") * 40000)
    open(D + "/page.html", "w").write("<html><body><h1>Title</h1><p>Para with <b>bold</b> and <i>italic</i>.</p><ul><li>one</li><li>two</li></ul><table><tr><td>a</td><td>b</td></tr></table></body></html>")
    open(D + "/data.csv", "w").write("a,b,c\n1,2,3\n")
    open(D + "/bin.pdf", "wb").write(b"%PDF-1.4\n%garbage")
    for f, expect in (("missing.docx", "error"), ("zero.docx", "error"), ("text.docx", "error"), ("plain.txt", "Line four"), ("latin1.txt", "café"), ("utf16.txt", "UTF sixteen"),
                      ("page.html", "Title"), ("data.csv", None), ("bin.pdf", None), ("", "error")):
        before = body_text()
        t0 = time.time(); opened(D + "/" + f if f else D); yield 2.0
        if expect == "error":
            check("opening %s is refused with a message, no traceback" % (f or "a folder"), MSG and not ERRS, (MSG, ERRS))
        elif expect:
            check("opening %s shows its text" % f, expect in body_text() and not ERRS, (MSG, ERRS, body_text()[:60]))
        else:
            note("opening %s" % f, (MSG, ERRS, body_text()[:50]))
        note("after " + (f or "folder"), "title=%r modified=%s" % (win.get_title(), ed().modified))
    t0 = time.time(); opened(D + "/big.txt")
    while time.time() - t0 < 90 and "word word" not in (ed().page_text(0) if ed().page_count() else ""):
        yield 0.5
    dt = time.time() - t0
    note("big.txt (40,000 lines)", "%.1fs, %d pages" % (dt, ed().page_count()))
    check("a 40,000-line text file opens in under 20 s", dt < 20, dt)
run_scenarios(a)
