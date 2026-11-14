import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
# W5-07: a page written as .html reads back as the same document.
HTML = "/tmp/n55.html"

def make_png(path, colour=(200, 60, 60)):
    from PIL import Image
    Image.new("RGB", (48, 32), colour).save(path)

def state():
    """What the document says about each marked word."""
    out = {}
    for w, key in (("bold", "bold"), ("italic", "italic"), ("strike", "strike")):
        r = find(w)
        out[w] = bool(r and r.run().get(key))
    for w in ("subscript", "superscript"):
        r = find(w)
        out[w] = r.run().get("vert_align") if r else None
    r = find("marked")
    out["highlight"] = r.run().get("highlight") if r else None
    out["link"] = link_here(find("linked")) if find("linked") else ""
    out["heading"] = style_of(0)
    out["tables"] = tables()
    out["pictures"] = len(objects())
    out["listed"] = is_listed(next((i for i, t in enumerate(para_texts()) if t == "a bullet"), 0))
    return out

def build():
    ed = E.ed
    ed.select_all(); ed.delete(True, False)
    ed.type_text("A heading\nplain bold italic strike subscript superscript marked linked\na bullet\n")
    E.view.after_edit()
    win.actions.apply_style("Heading 1")
    p0 = top_paras()[0]
    ed.select_nodes(p0, 0, p0, 0)
    win.actions.apply_style("Heading 1")
    find("bold").select(); ed.toggle("w:b")
    find("italic").select(); ed.toggle("w:i")
    find("strike").select(); ed.toggle("w:strike")
    find("subscript").select(); ed.apply_run([("w:vertAlign", [("w:val", "subscript")])], "Subscript")
    find("superscript").select(); ed.apply_run([("w:vertAlign", [("w:val", "superscript")])], "Superscript")
    find("marked").select(); ed.apply_run([("w:highlight", [("w:val", "yellow")])], "Highlight")
    find("linked").select(); ed.insert_hyperlink("https://example.com/x", None)
    r = find("a bullet"); r.caret_to_start(); ed.toggle_list("bullet")
    ed.move_caret("doc_end", False)
    ed.insert_table(2, 2)
    E.view.after_edit()

def a():
    yield 1.0
    focus(); yield 0.2
    ed = E.ed
    build(); yield 0.6
    make_png("/tmp/n55.png")
    ed.move_caret("doc_end", False)
    insert_picture("/tmp/n55.png"); yield 0.5
    ed.move_caret("doc_end", False)
    ed.insert_note(False); yield 0.4
    ed.type_text("a note"); E.view.after_edit(); yield 0.3
    ed.edit_notes(None); yield 0.4
    before = state()
    check("set up as expected", before["bold"] and before["highlight"] == "yellow"
          and before["pictures"] == 1 and before["tables"], str(before))
    win.save_to(HTML); yield 1.5
    h = open(HTML, encoding="utf-8").read()
    for frag in ("<b>", "<i>", "<s>", "<sub>", "<sup>", "background:", "href=", "<table", "<img ",
                 "<h1", "Footnotes", "a note"):
        check("the page carries %r" % frag, frag in h)
    win.engine.open(HTML); yield 3.5
    after = state()
    for key in ("bold", "italic", "strike", "subscript", "superscript", "highlight", "link"):
        check("%s came back" % key, after[key] == before[key], "%r -> %r" % (before[key], after[key]))
    check("the heading came back", (after["heading"] or "").startswith("Heading"), str(after["heading"]))
    check("the table came back", after["tables"] and len(after["tables"][0]) == 2, str(after["tables"]))
    check("the picture came back", after["pictures"] == 1, str(after["pictures"]))
    check("the bullet came back", after["listed"], str(after["listed"]))
    check("the note's words came back", "a note" in text(), text()[-80:])
    E.ed.mark_saved()

run_scenarios(a)
