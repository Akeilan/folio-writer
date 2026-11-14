import os as _o; TESTS = _o.environ["FOLIO_WRITER_TESTS"]; exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read()); exec(open("/tmp/p5/probes/ph.py").read())
import sys
ERRS = []; MSG = []
sys.excepthook = lambda t, v, tb: ERRS.append("%s: %s @%s" % (t.__name__, str(v)[:120], traceback.extract_tb(tb)[-1].name))
win.dialogs.message = lambda *a, **k: MSG.append(str(a[0])[:140] if a else "")
FL = []
_f = win.status.flash
win.status.flash = lambda m, *a, **k: (FL.append(str(m)[:100]), _f(m, *a, **k))[1]
WANT = ["Bullets > ◦  Open bullet", "Paragraph Spacing > Open", "Rules > Merge Record #", "Rules > Next Record", "Rules > Next Record If...", "Rules > Skip Record If...",
        "First Record", "Previous Record", "Next Record", "Last Record", "Print Layout", "Macros (Alt+F8) > View Macros", "Macros (Alt+F8) > Record Macro...",
        "Help (F1)", "Read Aloud (Ctrl+Alt+Space)", "Cover Page > Save Selection to Cover Page Gallery...", "Quick Parts > Save Selection to Quick Part Gallery...",
        "Header > Save Selection to Header Gallery...", "Text Box > Save Selection to Text Box Gallery...", "New Window", "Outline", "Close Outline View",
        "Immersive Reader", "Close Immersive Reader", "Read Mode", "Web Layout", "Draft", "Side to Side", "Focus"]
def a():
    yield 0.5
    focus(); fresh(); T("Alpha beta gamma.\nSecond paragraph here.\nThird."); yield 0.3
    _load_items()
    for lab in WANT:
        if lab not in _ITEMS:
            note("no control", lab); continue
        fresh(); ed().type_text("Alpha beta gamma.\nSecond paragraph here.\nThird."); win.engine.view.after_edit(); yield 0.15
        find("beta").select(); yield 0.1
        del ERRS[:]; del MSG[:]; del FL[:]
        before = doc_xml()["word/document.xml"]
        nwin = len(win.app.windows)
        try:
            GLib.idle_add(lambda f=_ITEMS[lab][0][1]: (f(), False)[1])
        except Exception as e:
            ERRS.append(repr(e))
        yield 1.0
        d = [x.get_title() for x in dialogs_open()]
        after = doc_xml()["word/document.xml"]
        note(lab, "dialogs=%s msg=%s flash=%s err=%s changed=%s windows=%d->%d view=%s" % (d, MSG[:2], FL[:2], ERRS[:2], before != after, nwin, len(win.app.windows), ed().view_mode()))
        if ERRS: check("%s runs without an error" % lab, False, ERRS[:2])
        close_dialogs(); yield 0.3
        for w in list(win.app.windows)[1:]:
            try: w.engine.ed.mark_saved(); w.close()
            except Exception: pass
        K("Escape"); yield 0.2
        try:
            if ed().view_mode() != 0: win.act_print_layout()
        except Exception: pass
        yield 0.2
run_scenarios(a)
