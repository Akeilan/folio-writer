import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
# W5-15: emoji drawn in colour, and a skin-tone modifier drawn as one emoji.
from PIL import Image

def area(name, p, a, b):
    """The screen pixels of the text [a, b) of paragraph p."""
    ed = E.ed
    r = ed.range_rects(p, a, p, b)[0]
    x0, y0 = doc_screen(r[1] * 20, r[2] * 20)
    x1, y1 = doc_screen((r[1] + r[3]) * 20, (r[2] + r[4]) * 20)
    shot(name)
    im = Image.open("/tmp/fshot_%s.png" % name).convert("RGB")
    return im.crop((int(x0), int(y0), max(int(x1), int(x0) + 1), max(int(y1), int(y0) + 1)))

def colours(im):
    """How many clearly coloured (not grey) pixels, and how many distinct hues."""
    vivid = [(r, g, b) for (r, g, b) in im.getdata() if max(r, g, b) - min(r, g, b) > 40]
    return len(vivid), len(set((r // 48, g // 48, b // 48) for r, g, b in vivid))

def put(s):
    ed = E.ed
    ed.select_all(); ed.delete(True, False)
    ed.apply_run([("w:sz", [("w:val", "72")])], "Size")
    ed.type_text(s)
    E.view.after_edit()
    return ed.body_blocks()[0][1]

def a():
    yield 1.0
    focus(); yield 0.2
    ed = E.ed
    p = put("\U0001F600"); yield 0.8
    im = area("emoji1", p, 0, 1)
    n, hues = colours(im)
    check("a grinning face is drawn in colour", n > 40, "%d coloured pixels" % n)
    check("it has several colours", hues >= 2, "%d hues" % hues)
    # a skin-tone modifier is part of the emoji, not a box of its own
    p = put("\U0001F44D\U0001F3FD"); yield 0.8
    w_mod = ed.range_rects(p, 0, p, 2)[0][3]
    p2 = put("\U0001F44D"); yield 0.6
    w_plain = ed.range_rects(p2, 0, p2, 1)[0][3]
    check("thumbs up with a skin tone is one emoji wide", abs(w_mod - w_plain) < w_plain * 0.3,
          "%.2f vs %.2f" % (w_mod, w_plain))
    p = put("\U0001F44D\U0001F3FD"); yield 0.8
    im = area("emoji2", p, 0, 2)
    n2, _h = colours(im)
    check("the skin tone is drawn in colour", n2 > 40, "%d coloured pixels" % n2)
    # a flag is one picture from its two regional indicators
    p = put("\U0001F1F3\U0001F1F1"); yield 0.8
    im = area("flag", p, 0, 2)
    n3, h3 = colours(im)
    check("a flag is drawn in colour", n3 > 40, "%d coloured pixels" % n3)
    check("the flag has several colours", h3 >= 2, "%d hues" % h3)
    # text symbols stay text: a tick is not turned into a picture
    p = put("✓"); yield 0.6
    im = area("tick", p, 0, 1)
    n4, _ = colours(im)
    check("a tick is still drawn as text", n4 < 20, "%d coloured pixels" % n4)
    # emoji survive a save
    p = put("\U0001F600\U0001F44D\U0001F3FD"); yield 0.5
    win.save_to("/tmp/n54.docx"); yield 0.6
    import zipfile
    d = zipfile.ZipFile("/tmp/n54.docx").read("word/document.xml").decode()
    check("emoji saved", "\U0001F600" in d and "\U0001F3FD" in d)
    E.ed.mark_saved()

run_scenarios(a)
