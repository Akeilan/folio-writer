# W5-08, W5-09: text files in any encoding, opened quickly.
import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d)))
exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
import tempfile
from folio.native import plaintext

D = tempfile.mkdtemp(prefix="n48_")
LOADED = {"n": 0}
_l = win._loaded
def _loaded(ok):
    LOADED["n"] += 1
    return _l(ok)
win._loaded = _loaded

def wrote(name, data):
    p = os.path.join(D, name)
    with open(p, "wb") as f:
        f.write(data)
    return p

def opened(p, timeout=120):
    n = LOADED["n"]
    t0 = time.time()
    win.open_file(p)
    while LOADED["n"] == n and time.time() - t0 < timeout:
        pump(0.05)
    return time.time() - t0

def body():
    E.ed.select_all()
    t = E.ed.selected_text()
    E.ed.move_caret("doc_start", False)
    return t

def encodings():
    yield 0.4
    cases = [("utf8.txt", "café naïve ✓\nsecond line\n".encode("utf-8"), "café naïve ✓"),
             ("latin1.txt", "café naïve\nsecond line\n".encode("latin-1"), "café naïve"),
             ("cp1252.txt", "“smart” — dash\n".encode("cp1252"), "“smart” — dash"),
             ("utf16.txt", "UTF sixteen ✓\nsecond line\n".encode("utf-16"), "UTF sixteen ✓"),
             ("utf16le.txt", "no mark here\n".encode("utf-16-le"), "no mark here"),
             ("utf8bom.txt", "﻿with a mark\n".encode("utf-8-sig"), "with a mark"),
             ("empty.txt", b"", ""),
             ("nonl.txt", b"no newline at the end", "no newline at the end")]
    for name, data, want in cases:
        p = wrote(name, data)
        opened(p); yield 0.5
        t = body()
        check("%s reads as text, not rubbish" % name, want in t and "�" not in t, repr(t[:60]))
    # tabs and blank lines survive
    p = wrote("tabs.txt", b"a\tb\tc\n\nlast\n")
    opened(p); yield 0.5
    check("tabs are kept", "a\tb\tc" in body().replace("\u0009", "\t"), repr(body()[:40]))
    check("a blank line is a paragraph", len([x for x in body().split("\n")]) >= 3, repr(body()))

def speed():
    yield 0.3
    big = ("word " * 12 + "\n") * 40000
    p = wrote("big.txt", big.encode("utf-8"))
    secs = opened(p)
    note("40,000 lines", "%.1fs, %d pages" % (secs, E.ed.page_count()))
    check("a 40,000-line text file opens in under 20 s", secs < 20, secs)
    check("and all of it is there", E.ed.page_count() > 100, E.ed.page_count())

def unit():
    yield 0.2
    check("a byte-order mark names the encoding", plaintext.encoding_of("x".encode("utf-16")) == "utf-16")
    check("UTF-16 without a mark is still found", plaintext.encoding_of("hello there".encode("utf-16-le")) == "utf-16-le")
    check("plain ASCII reads as UTF-8", plaintext.encoding_of(b"plain ascii") == "utf-8")
    check("an 8-bit file falls back", plaintext.encoding_of("café".encode("latin-1")) in ("cp1252", "latin-1"))
    check("control characters XML can't hold are dropped", "\x07" not in plaintext.paragraphs_xml("a\x07b"))
    check("and the text around them stays", "ab" in plaintext.paragraphs_xml("a\x07b"))
run_scenarios(encodings, speed, unit)
