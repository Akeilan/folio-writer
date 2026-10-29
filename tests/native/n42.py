import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
# 2.32 (W3-09): AutoFormat the whole document; Define styles based on your formatting
import zipfile

from folio import autoformatdlg

MSG = []
win.dialogs.message = lambda text, *a, **k: MSG.append(text)


def body(ed):
    return [ed.para_text_of(n) for k, n, _t in ed.body_blocks() if k == "p"]


def xml(ed):
    ed.save("/tmp/n42.docx")
    return zipfile.ZipFile("/tmp/n42.docx").read("word/document.xml").decode()


def style_of(ed, text):
    for k, n, _t in ed.body_blocks():
        if k == "p" and ed.para_text_of(n).startswith(text):
            ed.select_nodes(n, 0, n, 0)
            return (ed.state() or {}).get("style")


def a():
    yield 1.0
    s = win.app.settings
    for k in ("ac_quotes", "ac_dashes", "ac_bullets", "ac_numbers", "ac_replace", "ac_caps_first",
              "ac_urls", "ac_ordinals", "ac_fractions", "ac_bold_italic", "ac_headings", "ac_define_styles"):
        s[k] = False                    # typed as plain text first
    ed = E.ed
    lines = ["Project Overview",
             "This report explains the \"plan\" for the year -- with a lot of detail in every line.",
             "* first point",
             "* second point",
             "1. step one",
             "2. step two",
             "Results",
             "We finished 1st and spent 1/2 of the budget, see www.example.org for *all* the _details_ here."]
    ed.type_text("\n".join(lines))
    E.view.after_edit(); yield 0.3
    check("typed plain", style_of(ed, "Project Overview") == "Normal" and '"plan"' in str(body(ed)))
    # ---- AutoFormat now
    done = autoformatdlg.autoformat_now(win); yield 0.5
    b = body(ed)
    x = xml(ed)
    check("headings", style_of(ed, "Project Overview") == "Heading 1" and style_of(ed, "Results") == "Heading 1",
          (style_of(ed, "Project Overview"), style_of(ed, "Results"), done))
    check("body text style", style_of(ed, "This report") == "Body Text", style_of(ed, "This report"))
    check("bulleted list", "first point" in b and "* first point" not in b and x.count("<w:numPr>") >= 4, b)
    check("numbered list", "step one" in b and "1. step one" not in b, b)
    check("smart quotes", "“plan”" in str(b), b[1])
    check("dash", "year – with" in str(b) or "year—with" in str(b), b[1])
    check("fraction", "½" in str(b), b[-1])
    check("ordinal superscript", 'w:vertAlign w:val="superscript"' in x)
    check("bold and italic", "*all*" not in str(b) and "_details_" not in str(b) and "<w:b/>" in x and "<w:i/>" in x, b[-1])
    check("link", "www.example.org" in x and "<w:hyperlink" in x)
    # ---- one undo step takes it all back (Reject All)
    ed.undo()
    E.view.after_edit(); yield 0.3
    check("undo restores", '"plan"' in str(body(ed)) and style_of(ed, "Project Overview") == "Normal", body(ed)[:2])
    # ---- the dialog: AutoFormat and review, Reject All
    import folio.autoformatdlg as AFD
    orig = AFD.FDialog.ask
    answers = []

    def ask(self):
        self.show_all()
        if self.get_title() == "AutoFormat" and not answers:
            answers.append("first")
            for w in _all(self):
                if hasattr(w, "set_active") and hasattr(w, "get_label") and (w.get_label() or "").endswith("review each change"):
                    w.set_active(True)
            return -5
        answers.append("review")
        return 2
    AFD.FDialog.ask = ask
    try:
        AFD.dialog(win)
    finally:
        AFD.FDialog.ask = orig
    yield 0.3
    check("review offered", answers == ["first", "review"], answers)
    check("reject all keeps the text", '"plan"' in str(body(ed)), body(ed)[:2])
    # ---- options: the AutoFormat tab's choices are used
    s["af_headings"] = False
    autoformatdlg.autoformat_now(win); yield 0.3
    check("headings option off", style_of(ed, "Project Overview") != "Heading 1", style_of(ed, "Project Overview"))
    s["af_headings"] = True
    ed.undo()
    # ---- Define styles based on your formatting (as you type)
    s["ac_define_styles"] = True
    ed.select_all()
    ed.delete(True, False)
    E.view.after_edit(); yield 0.2
    ed.type_text("Big Title Line")
    ed.select_all()
    ed.apply_run([("w:b", []), ("w:sz", [("w:val", "40")]), ("w:szCs", [("w:val", "40")])], "Font")
    ed.select_nodes(ed.caret_pos()[0], 14, ed.caret_pos()[0], 14)
    E.view.after_edit(); yield 0.2
    ac = getattr(win, "autocorrect", None) or getattr(E, "autocorrect", None)
    if ac is None:
        from folio.native.autocorrect import AutoCorrect
        ac = AutoCorrect(win)
    ac.before_break()
    E.view.after_edit(); yield 0.2
    check("formatted line becomes a heading", style_of(ed, "Big Title") == "Heading 1", style_of(ed, "Big Title"))
    ids = {n: i for i, n in ed.paragraph_styles()}
    rv = ed.style_run_values(ids["Heading 1"])
    check("the heading style takes the formatting", rv.get("bold") and abs(rv.get("size", 0) - 20) < 0.1, dict(rv))
    s["ac_define_styles"] = False
    ed.mark_saved()


def _all(w):
    out = [w]
    if hasattr(w, "get_children"):
        for c in w.get_children():
            out += _all(c)
    return out


run_scenarios(a)
