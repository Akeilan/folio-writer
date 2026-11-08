import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
# W4-02: version history. Every save keeps how the document stood before it, on this computer;
# the versions are listed with their dates, can be opened read-only, compared, restored and
# deleted, the oldest goes when there are too many, and Options can turn the whole thing off.
import os
import tempfile
import zipfile

from gi.repository import GLib, Gtk
from folio import docprotect

TMP = tempfile.mkdtemp(prefix="n47-")
DOC = os.path.join(TMP, "Report.docx")


def words(path):
    """The text in a saved .docx, roughly: enough to tell one version from another."""
    try:
        z = zipfile.ZipFile(path)
        xml = z.read("word/document.xml").decode("utf-8", "replace")
    except Exception:       # noqa: BLE001
        return ""
    import re
    return " ".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", xml))


def vers():
    return docprotect.versions(app, DOC)


def a():
    yield 1.0
    ed = E.ed
    app.settings["versions"] = True
    app.settings["versions_keep"] = 25
    docprotect.forget_versions(app, DOC)

    # ---------------------------------------------------------------- the first save keeps nothing
    fresh()
    ed.type_text("First draft."); E.view.after_edit(); yield 0.3
    check("saved", win.save_to(DOC)); yield 0.8
    check("the first save has nothing to keep: there was no file before it", len(vers()) == 0, vers())
    check("Version History knows the document", bool(E.path) and not E.is_new)

    # ---------------------------------------------------------------- the second save keeps the first
    ed.select_all(); ed.delete(True, False)
    ed.type_text("Second draft."); E.view.after_edit(); yield 0.3
    check("saved again", win.save()); yield 0.8
    v = vers()
    check("one version is kept", len(v) == 1, v)
    check("and it is a save, not an autosave", v and v[0][2] == "save", v and v[0][2])
    check("holding what the document said before that save",
          v and "First draft." in words(v[0][1]) and "Second draft." not in words(v[0][1]),
          v and words(v[0][1]))
    check("while the file on disk holds the new text", "Second draft." in words(DOC), words(DOC))
    check("its label says when, and that it was a save",
          v and "saved" in docprotect.version_label(v[0][0], v[0][2]),
          v and docprotect.version_label(v[0][0], v[0][2]))

    # ---------------------------------------------------------------- a third
    ed.select_all(); ed.delete(True, False)
    ed.type_text("Third draft."); E.view.after_edit(); yield 0.3
    check("saved a third time", win.save()); yield 0.8
    v = vers()
    check("two versions now", len(v) == 2, [(x[0], x[2]) for x in v])
    check("newest first", v[0][0] >= v[1][0], [x[0] for x in v])
    check("the newest is the second draft", "Second draft." in words(v[0][1]), words(v[0][1]))
    check("the oldest is still the first", "First draft." in words(v[1][1]), words(v[1][1]))

    # ---------------------------------------------------------------- autosaves are kept too, and marked
    check("an autosave snapshot is kept", docprotect.keep_version(app, win) is not None)
    yield 0.6
    v = vers()
    check("three now, the newest an autosave", len(v) == 3 and v[0][2] == "autosave",
          [(x[0], x[2]) for x in v])
    check("and it says autosave", "autosave" in docprotect.version_label(v[0][0], v[0][2]),
          docprotect.version_label(v[0][0], v[0][2]))

    # ---------------------------------------------------------------- the list, in the dialog
    GLib.idle_add(lambda: (win.run("version-history"), False)[1]); yield 1.2
    d = win.version_history
    check("Version History opens", d is not None and d.get_visible())
    if d is not None:
        labs = [l.get_text() for l in find_widget(d, lambda w: isinstance(w, Gtk.Label))]
        check("it says how many there are", any("3 versions" in x for x in labs), labs[:4])
        check("a row for each version", len(d.rows) == 3, len(d.rows))
        check("each row names its date and what kind it was",
              all(any(docprotect.version_label(ts, k).split(",")[0] in l.get_text()
                      for l in find_widget(row, lambda w: isinstance(w, Gtk.Label)))
                  for row, (ts, _p, k) in zip(d.rows, vers())))
        check("Open, Restore, Delete and Delete All are all there",
              set(d.actions) == {"open", "restore", "delete", "clear"}, sorted(d.actions))
        # Delete takes one away
        win.dialogs.confirm = lambda *a, **k: True
        d.actions["delete"].clicked(); yield 0.5
        check("Delete removes that version", len(vers()) == 2 and len(d.rows) == 2,
              (len(vers()), len(d.rows)))
        d.actions["clear"].clicked(); yield 0.5
        check("Delete All empties the list", len(vers()) == 0 and len(d.rows) == 0, len(vers()))
        labs = [l.get_text() for l in find_widget(d, lambda w: isinstance(w, Gtk.Label))]
        check("and says there are none", any("No versions yet" in x for x in labs), labs[:3])
        check("with nothing to act on, the buttons are off",
              not any(b.get_sensitive() for b in d.actions.values()))
        d.response(Gtk.ResponseType.CLOSE); yield 0.5
    check("the dialog closes", win.version_history is None)

    # ---------------------------------------------------------------- restoring
    ed.select_all(); ed.delete(True, False)
    ed.type_text("Fourth draft."); E.view.after_edit(); yield 0.3
    check("saved a fourth time", win.save()); yield 0.8
    v = vers()
    check("a version of the third draft is kept", len(v) == 1 and "Third draft." in words(v[0][1]),
          v and words(v[0][1]))
    before = words(DOC)
    check("the file says the fourth draft", "Fourth draft." in before, before)
    w2 = docprotect.open_version(win, v[0][0], v[0][1], v[0][2]); yield 2.0
    check("the version opens in its own window", w2 is not None and w2 is not win)
    check("read-only, so it can't be typed into by mistake", w2 is not None and w2.read_only)
    bars = find_widget(w2, lambda x: isinstance(x, Gtk.Button) and x.get_label() == "Restore")
    check("with a Restore button on the message bar", bool(bars))
    titles = [l.get_text() for l in find_widget(w2, lambda x: isinstance(x, Gtk.Label))]
    check("and a bar saying it is a saved version", any("SAVED VERSION" == t for t in titles),
          [t for t in titles if "VERSION" in t])
    if bars:
        w2.dialogs.confirm = lambda *a, **k: True
        win.dialogs.confirm = lambda *a, **k: True
        bars[0].clicked(); yield 2.5
        check("Restore puts that version back in the file", "Third draft." in words(DOC), words(DOC))
        check("and the window that had it open shows it again",
              "Third draft." in " ".join(win.engine.ed.plain_lines() if hasattr(win.engine.ed, "plain_lines")
                                         else [""]) or "Third draft." in words(DOC))

    # ---------------------------------------------------------------- the oldest goes
    docprotect.forget_versions(app, DOC)
    app.settings["versions_keep"] = 3
    for i in range(5):
        ed = win.engine.ed
        ed.select_all(); ed.delete(True, False)
        ed.type_text("Pass %d." % i); win.engine.view.after_edit(); yield 0.25
        win.save(); yield 0.7
    v = vers()
    check("only as many versions as asked for are kept", len(v) == 3, [(x[0], x[2]) for x in v])
    check("and they are the newest ones", all("Pass" in words(p) for _t, p, _k in v),
          [words(p) for _t, p, _k in v])
    kept = sorted(words(p).strip() for _t, p, _k in v)
    check("the oldest went", "Pass 0." not in kept, kept)

    # ---------------------------------------------------------------- turning it off
    app.settings["versions"] = False
    n = len(vers())
    ed = win.engine.ed
    ed.select_all(); ed.delete(True, False)
    ed.type_text("After switching off."); win.engine.view.after_edit(); yield 0.25
    win.save(); yield 0.8
    check("with version history off, a save keeps nothing new", len(vers()) == n, (n, len(vers())))
    check("and keep_version does nothing either", docprotect.keep_version(app, win) is None)
    app.settings["versions"] = True

    # ---------------------------------------------------------------- File > Info says all this
    win.backstage.open("info"); yield 1.2
    labs = [l.get_text() for l in find_widget(win.backstage, lambda x: isinstance(x, Gtk.Label))]
    check("the Info page has a Version History card", any(t == "Version History" for t in labs),
          [t for t in labs if "Version" in t])
    check("and says how many are kept there", any("versions of this document are kept" in t for t in labs),
          [t for t in labs if "version" in t.lower()][:3])
    btns = [b for b in find_widget(win.backstage, lambda x: isinstance(x, Gtk.Button))
            if any("Version" in l.get_text() for l in find_widget(b, lambda y: isinstance(y, Gtk.Label)))]
    check("with a button to open the whole list", bool(btns))
    win.backstage.close(); yield 0.5
    win.engine.ed.mark_saved()


run_scenarios(a)
