import zipfile, re, json
OUTD = '/tmp/p5out/rt'; os.makedirs(OUTD, exist_ok=True)
PIC = os.path.join(os.environ['FOLIO_SHARE'], 'icons', 'folio-page-128.png')
TAGS = ["w:tbl", "w:tc", "w:drawing", "w:pict", "w:footnoteReference", "w:endnoteReference", "w:commentReference", "w:ins", "w:del",
        "w:hyperlink", "w:bookmarkStart", "w:sdt", "w:fldChar", "w:fldSimple", "m:oMath", "w:numPr", "w:b", "w:i", "w:u",
        "w:highlight", "w:strike", "w:vertAlign", "w:txbxContent"]
def inventory():
    p = OUTD + "/_inv.docx"
    ed().save(p)
    inv = {}
    with zipfile.ZipFile(p) as z:
        doc = z.read("word/document.xml").decode("utf8", "replace")
        for t in TAGS:
            inv[t] = cnt(doc, t)
        inv["heading1"] = len(re.findall(r'w:pStyle w:val="Heading1"', doc))
        inv["red"] = len(re.findall(r'w:color w:val="FF0000"', doc))
        inv["size20"] = len(re.findall(r'<w:sz w:val="40"', doc))
        inv["serif"] = len(re.findall(r'w:ascii="Liberation Serif"', doc))
        inv["center"] = len(re.findall(r'<w:jc w:val="center"', doc)); inv["right"] = len(re.findall(r'<w:jc w:val="(right|end)"', doc))
        names = z.namelist()
        inv["hdr_text"] = sorted(set(re.sub(r"<[^>]+>", "", z.read(n).decode("utf8", "replace")).strip()[:40] for n in names if re.match(r"word/(header|footer)\d*\.xml", n)) - {""})
        inv["media"] = len([n for n in names if n.startswith("word/media/")])
        inv["comments"] = cnt(z.read("word/comments.xml").decode("utf8", "replace"), "w:comment") if "word/comments.xml" in names else 0
        inv["footnotes"] = max(0, cnt(z.read("word/footnotes.xml").decode("utf8", "replace"), "w:footnote") - 2) if "word/footnotes.xml" in names else 0
        inv["endnotes"] = max(0, cnt(z.read("word/endnotes.xml").decode("utf8", "replace"), "w:endnote") - 2) if "word/endnotes.xml" in names else 0
        inv["text"] = re.sub(r"<[^>]+>", "", re.sub(r"</w:p>", "\n", re.sub(r"<w:tab/>", "\t", doc)))
    inv["pages"] = ed().page_count()
    return inv

def step(name, fn):
    try:
        r = fn()
        return r
    except Exception as e:
        check("build: " + name, False, repr(e)[:200])

def build():
    e = ed()
    T("Round Trip Heading"); win.run(("style", "Heading 1")); T("\n")
    T("Plain then "); K("ctrl+b"); T("bold"); K("ctrl+b")
    T(" then "); K("ctrl+i"); T("italic"); K("ctrl+i")
    T(" then "); K("ctrl+u"); T("underlined"); K("ctrl+u")
    T(" then "); R("Font Color > #FF0000"); T("red"); R("Font Color > Automatic")
    T(" then "); R("Text Highlight Color > Yellow"); T("marked"); R("Text Highlight Color > No Color")
    T(" then "); e.set_size(20.0); T("big"); e.set_size(11.0)
    T(" then "); e.set_font("Liberation Serif"); T("serif"); e.set_font("Carlito")
    T(" then "); R("Strikethrough"); T("struck"); R("Strikethrough")
    T(" H"); K("ctrl+equal"); T("2"); K("ctrl+equal"); T("O.\n")
    K("ctrl+e"); T("Centred line\n"); K("ctrl+r"); T("Right line\n"); K("ctrl+l")
    step("bullets", lambda: (R("Bullets"), T("First bullet\nSecond bullet\nThird bullet\n\n")))
    step("numbers", lambda: (R("Numbering"), T("One\nTwo\nThree\n\n")))
    def table():
        e.insert_table(3, 3); pump(0.2)
        for i in range(9):
            T("c%d" % i)
            if i < 8: K("Tab")
        K("ctrl+End")
    step("table", table)
    T("After the table. Footnote here")
    step("footnote", lambda: (R("Insert Footnote (Ctrl+Alt+F)"), T("The footnote text."), e.edit_notes(None)))
    K("ctrl+End"); T(" and endnote here")
    step("endnote", lambda: (R("Insert Endnote (Ctrl+Alt+D)"), T("The endnote text."), e.edit_notes(None)))
    K("ctrl+End"); T("\n")
    step("picture", lambda: (e.insert_picture(PIC), win.engine.view.after_edit(), e.deselect_object()))
    K("ctrl+End"); T("\nLink: ")
    step("hyperlink", lambda: e.insert_hyperlink("https://example.org/", "Example"))
    K("ctrl+End"); T("\nBookmarked words here")
    step("bookmark", lambda: (K("ctrl+shift+Left"), e.add_bookmark("mark1")))
    K("ctrl+End"); T("\nCommented words here")
    step("comment", lambda: (K("ctrl+shift+Left"), e.insert_comment("A remark", "Tester")))
    K("ctrl+End"); T("\nTracked: ")
    step("track", lambda: (R("Track Changes (Ctrl+Shift+E)"), T("inserted while tracking"), R("Track Changes (Ctrl+Shift+E)")))
    T("\nControl: ")
    step("control", lambda: R("Plain Text Content Control"))
    K("ctrl+End"); T("\n")
    step("shape", lambda: (e.insert_shape("rect", 0, 300, 600, 120, 60, "Rectangle 1", False), win.engine.view.after_edit(), e.deselect_object()))
    K("ctrl+End")
    step("header", lambda: (R("Header > Edit Header"), T("Header words"), win.run("close-header-footer")))
    step("footer", lambda: (R("Footer > Edit Footer"), T("Footer words"), win.run("close-header-footer")))
    K("ctrl+End")

def diff(a, b, lossy=()):
    out = []
    for k in a:
        if k in lossy: continue
        if a[k] != b.get(k):
            if k == "text":
                import difflib
                sm = difflib.SequenceMatcher(None, a[k], b.get(k, ""))
                ops = [(t, a[k][i1:i2][:30], b[k][j1:j2][:30]) for t, i1, i2, j1, j2 in sm.get_opcodes() if t != "equal"][:6]
                out.append("text: %r" % (ops,))
            else:
                out.append("%s: %r -> %r" % (k, a[k], b.get(k)))
    return out

