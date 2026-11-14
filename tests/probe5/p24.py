import os as _o; TESTS = _o.environ["FOLIO_WRITER_TESTS"]; exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read()); exec(open("/tmp/p5/probes/ph.py").read())
MSG = []
win.dialogs.message = lambda *a, **k: MSG.append(str(a[0])[:140] if a else "")
def a():
    yield 0.5
    focus(); fresh(); T("Alpha beta gamma.\nSecond paragraph here."); yield 0.3
    K("ctrl+Home"); K("shift+End"); yield 0.3
    note("selection", repr(sel()))
    for lab in ("Quick Parts > Save Selection to Quick Part Gallery...", "Cover Page > Save Selection to Cover Page Gallery...", "Text Box > Save Selection to Text Box Gallery..."):
        del MSG[:]
        GLib.idle_add(lambda f=_ITEMS[lab][0][1] if _ITEMS or _load_items() or True else None: (f(), False)[1]); yield 1.0
        d = dialogs_open()
        note(lab, "dialogs=%s msg=%s sel=%r" % ([x.get_title() for x in d], MSG, sel()))
        check("%s sees the selection" % lab.split(" > ")[1], bool(d) and not MSG, MSG)
        close_dialogs(); yield 0.3
    # paragraph spacing presets
    for lab in ("Paragraph Spacing > Default", "Paragraph Spacing > Open", "Paragraph Spacing > Relaxed", "Paragraph Spacing > Open", "Paragraph Spacing > Compact", "Paragraph Spacing > Open"):
        _ITEMS[lab][0][1](); yield 0.3
        x = doc_xml()["word/styles.xml"]
        m = re.search(r"<w:pPrDefault>.*?</w:pPrDefault>", x, re.S)
        note(lab, re.sub(r"\s+", " ", m.group(0))[:200] if m else "no pPrDefault")
import re
_load_items()
run_scenarios(a)
