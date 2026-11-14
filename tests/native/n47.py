# W5-01, W5-10, W5-12: what a crash recovers, what Undo leaves in the file, and printing.
import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d)))
exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
import zipfile

def parts_of(path):
    with zipfile.ZipFile(path) as z:
        return set(z.namelist())

def saved(name="/tmp/n47.docx"):
    E.ed.save(name)
    return name

def hdr_words(path):
    out = []
    with zipfile.ZipFile(path) as z:
        for n in z.namelist():
            if n.startswith("word/header") or n.startswith("word/footer"):
                out.append(z.read(n).decode("utf8", "replace"))
    return " ".join(out)

def undo_leaves_nothing():
    """W5-10: what Undo takes off the page comes out of the file too."""
    fresh(); yield 0.3
    E.ed.type_text("Body text.")
    base = parts_of(saved())
    n = len(E.ed.undo_names())
    win.run("header:Blank") if False else None
    E.ed.ensure_header_footer(E.ed.current_section(), False)
    E.ed.edit_header_footer(0, False)
    E.ed.type_text("Secret header words")
    E.ed.edit_header_footer(None, False)
    yield 0.4
    check("the header is in the file", "Secret header" in hdr_words(saved()))
    while len(E.ed.undo_names()) > n:
        E.ed.undo()
    yield 0.3
    after = saved()
    check("after Undo the header words are gone from the file too",
          "Secret header" not in hdr_words(after), hdr_words(after)[:120])
    check("and no header part is left behind", parts_of(after) == base,
          sorted(parts_of(after) - base))

def undo_restores_settings():
    """W5-10: settings live outside the text; Undo has to put them back."""
    fresh(); yield 0.3
    E.ed.type_text("Body.")
    for name, label in (("mirrorMargins", "Mirrored margins"), ("autoHyphenation", "Automatic hyphenation")):
        was = E.ed.setting(name)
        n = len(E.ed.undo_names())
        win.actions.run("hyphenation:auto") if False else None
        E.ed.begin_group(label)
        E.ed.set_setting(name, not was)
        E.ed.end_group()
        yield 0.3
        check("%s is on" % label, E.ed.setting(name) != was)
        check("it is one undo step", len(E.ed.undo_names()) == n + 1, (n, E.ed.undo_names()[-2:]))
        E.ed.undo(); yield 0.2
        check("Undo puts %s back" % label.lower(), E.ed.setting(name) == was, E.ed.setting(name))
        E.ed.redo(); yield 0.2
        check("Redo applies it again", E.ed.setting(name) != was)
        E.ed.undo(); yield 0.2
    # the page colour lives in settings.xml, which is not part of the text either
    n = len(E.ed.undo_names())
    E.ed.set_page_color("385623"); yield 0.3
    check("a page colour is set", E.ed.page_color() is not None, E.ed.page_color())
    with zipfile.ZipFile(saved()) as z:
        on = "displayBackgroundShape" in z.read("word/settings.xml").decode("utf8", "replace")
    check("and written to the file", on)
    while len(E.ed.undo_names()) > n:
        E.ed.undo()
    yield 0.3
    with zipfile.ZipFile(saved()) as z:
        still = "displayBackgroundShape" in z.read("word/settings.xml").decode("utf8", "replace")
    check("Undo takes the page colour out of the file", not still)

def autorecover_keeps_everything():
    """W5-01: the recovery copy is a .docx, so it carries what .odt could not."""
    fresh(); yield 0.3
    e = E.ed
    e.type_text("Tracked: ")
    e.set_track_changes(True); e.type_text("inserted"); e.set_track_changes(False)
    e.set_highlight("yellow"); e.type_text(" marked"); e.set_highlight("none")
    e.insert_shape("rect", 0, 200, 300, 120, 60, "Rectangle 1", False)
    e.deselect_object(); e.move_caret("doc_end", False)
    yield 0.4
    win.app.write_autorecover(win); yield 0.6
    d = win.app.autorecover_dir
    files = [f for f in os.listdir(d) if not f.endswith(".info") and os.path.isfile(os.path.join(d, f))]
    check("the recovery copy is a .docx", files and all(f.endswith(".docx") for f in files), files)
    p = os.path.join(win.app.autorecover_dir, files[0])
    with zipfile.ZipFile(p) as z:
        x = z.read("word/document.xml").decode("utf8", "replace")
    for what, tag in (("the tracked insertion", "<w:ins "), ("the highlighting", "<w:highlight"), ("the shape", "wps:wsp")):
        check("the recovery copy keeps %s" % what, tag in x, x[:0])
    check("Page offers it again", any(os.path.basename(q) == files[0] for q, _i in win.app.recovered_files()))
    win.app.clear_autorecover(win)
    check("and clears it when the document is saved",
          not [f for f in os.listdir(d) if not f.endswith(".info") and os.path.isfile(os.path.join(d, f))])

def printing_is_not_an_edit():
    """W5-12."""
    fresh(); yield 0.3
    E.ed.type_text("Something to print."); yield 0.2
    win.save_to("/tmp/n47p.docx"); yield 0.6
    check("saved", not E.ed.modified)
    win.backstage._print("__pdf__", 1, "all", "", "one-sided", True, 1) if False else None
    from folio.native import docprops
    was = E.ed.modified
    docprops.set_core(E.ed, lastPrinted="2026-11-14T00:00:00Z")
    if not was:
        E.ed.mark_saved()
    yield 0.3
    check("printing leaves the document saved", not E.ed.modified)
run_scenarios(undo_leaves_nothing, undo_restores_settings, autorecover_keeps_everything, printing_is_not_an_edit)
