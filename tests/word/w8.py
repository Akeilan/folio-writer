import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
import importlib
def texts_of(w):
    out = []
    for x in find_widget(w, lambda x: True):
        try:
            if isinstance(x, Gtk.Label): out.append(x.get_text())
            elif isinstance(x, Gtk.Button) and x.get_label(): out.append(x.get_label())
            elif isinstance(x, Gtk.Entry) and x.get_placeholder_text(): out.append(x.get_placeholder_text())
            elif isinstance(x, Gtk.Notebook):
                for i in range(x.get_n_pages()):
                    tl = x.get_tab_label(x.get_nth_page(i))
                    for l in ([tl] if isinstance(tl, Gtk.Label) else find_widget(tl, lambda y: isinstance(y, Gtk.Label))):
                        out.append(l.get_text())
            elif isinstance(x, Gtk.TreeView) and x.get_model() is not None:
                out.extend(r[0] for r in x.get_model() if isinstance(r[0], str))
            elif isinstance(x, Gtk.ComboBoxText):
                m = x.get_model()
                out.extend(r[0] for r in m if isinstance(r[0], str))
        except Exception: pass
    return " | ".join(" ".join(t.replace("_", "").split()) for t in out if t)
D = win.dialogs
SPECS = [
 ("Font", lambda: D.font_dialog(), ["Font style", "Size", "Font color", "Underline style", "Underline color", "Strikethrough", "Double strikethrough", "Superscript", "Subscript", "Small caps", "All caps", "Hidden", "Advanced", "Scale", "Spacing", "Position", "Kerning", "Ligatures", "Number spacing", "Stylistic sets", "Preview", "Set As Default", "Text Effects"]),
 ("Paragraph", lambda: D.paragraph_dialog(), ["Alignment", "Outline level", "Collapsed by default", "Left", "Right", "Special", "Mirror indents", "Before", "After", "Don't add space between paragraphs of the same style", "Line spacing", "At", "Line and Page Breaks", "Widow/Orphan control", "Keep with next", "Keep lines together", "Page break before", "Suppress line numbers", "Don't hyphenate", "Tabs", "Set As Default", "Preview"]),
 ("Tabs", lambda: D.tabs_dialog(), ["Tab stop position", "Default tab stops", "Alignment", "Left", "Center", "Right", "Decimal", "Bar", "Leader", "Set", "Clear", "Clear All"]),
 ("Borders", lambda: D.borders_dialog(), ["Borders", "Page Border", "Shading", "Setting", "None", "Box", "Shadow", "3-D", "Custom", "Style", "Color", "Width", "Apply to", "Options", "Fill", "Pattern", "Art"]),
 ("Page Setup", lambda: D.page_setup(), ["Margins", "Top", "Bottom", "Left", "Right", "Gutter", "Gutter position", "Orientation", "Portrait", "Landscape", "Multiple pages", "Mirror margins", "Paper", "Paper size", "Paper source", "Layout", "Section start", "Different odd and even", "Different first page", "From edge", "Vertical alignment", "Line Numbers", "Borders", "Apply to", "Set As Default"]),
 ("Find", lambda: D.replace(), ["Find what", "Replace with", "Match case", "Find whole words only", "Use wildcards", "Sounds like", "Find all word forms", "Match prefix", "Match suffix", "Ignore punctuation", "Ignore white-space", "Format", "Special", "No Formatting", "Replace All", "Find Next", "Go To", "Reading Highlight", "Find In"]),
 ("Go To", lambda: D.goto(), ["Go to what", "Page", "Section", "Line", "Bookmark", "Comment", "Footnote", "Endnote", "Field", "Table", "Graphic", "Equation", "Heading", "Previous", "Next"]),
 ("Word Count", lambda: D.word_count(), ["Pages", "Words", "Characters (no spaces)", "Characters (with spaces)", "Paragraphs", "Lines", "Include textboxes, footnotes and endnotes"]),
 ("Hyperlink", lambda: D.hyperlink(), ["Existing File or Web Page", "Place in This Document", "Create New Document", "E-mail Address", "Text to display", "ScreenTip", "Address", "Bookmark", "Target Frame"]),
 ("Bookmark", lambda: D.bookmark(), ["Bookmark name", "Add", "Delete", "Go To", "Sort by", "Name", "Location", "Hidden bookmarks"]),
 ("Cross-reference", lambda: D.cross_reference(), ["Reference type", "Insert reference to", "Insert as hyperlink", "Include above/below", "For which", "Separate numbers with"]),
 ("Caption", lambda: D.caption(), ["Caption", "Label", "Position", "Exclude label from caption", "New Label", "Delete Label", "Numbering", "AutoCaption"]),
 ("Table of Contents", lambda: D.toc_dialog(), ["Print Preview", "Web Preview", "Show page numbers", "Right align page numbers", "Tab leader", "Formats", "Show levels", "Use hyperlinks", "Options", "Modify"]),
 ("Date and Time", lambda: D.date_time(), ["Available formats", "Language", "Update automatically", "Set As Default"]),
 ("Field", lambda: D.field_dialog(), ["Categories", "Field names", "Field properties", "Field options", "Field Codes", "Preserve formatting during updates"]),
 ("Symbol", lambda: D.symbol_dialog(), ["Symbols", "Special Characters", "Font", "Subset", "Recently used symbols", "Character code", "from", "AutoCorrect", "Shortcut Key"]),
 ("Insert Table", lambda: D.insert_table_dialog(), ["Number of columns", "Number of rows", "AutoFit behavior", "Fixed column width", "AutoFit to contents", "AutoFit to window", "Remember dimensions for new tables"]),
 ("Watermark", lambda: D.watermark_dialog(), ["No watermark", "Picture watermark", "Select Picture", "Scale", "Washout", "Text watermark", "Language", "Text", "Font", "Size", "Color", "Semitransparent", "Layout", "Diagonal", "Horizontal"]),
 ("Line Numbers", lambda: D.line_numbers_dialog(), ["Add line numbering", "Start at", "From text", "Count by", "Numbering", "Restart each page", "Restart each section", "Continuous"]),
 ("Drop Cap", lambda: D.drop_cap(), ["Position", "None", "Dropped", "In margin", "Font", "Lines to drop", "Distance from text"]),
 ("Sort", lambda: D.sort_dialog(), ["Sort by", "Type", "Using", "Ascending", "Descending", "Then by", "My list has", "Header row", "No header row", "Options"]),
 ("Zoom", lambda: D.zoom_dialog(), ["Zoom to", "200%", "100%", "75%", "Page width", "Text width", "Whole page", "Many pages", "Percent", "Preview"]),
 ("Index", lambda: D.insert_index(), ["Print Preview", "Type", "Indented", "Run-in", "Columns", "Language", "Right align page numbers", "Tab leader", "Formats", "Mark Entry", "AutoMark", "Modify"]),
 ("Table of Figures", lambda: D.table_of_figures(), ["Print Preview", "Show page numbers", "Right align page numbers", "Tab leader", "Caption label", "Include label and number", "Use hyperlinks", "Options", "Modify"]),
 ("Language", lambda: D.language_dialog(), ["Mark selected text as", "Do not check spelling or grammar", "Detect language automatically", "Set As Default"]),
 ("Paste Special", lambda: D.paste_special(), ["Source", "Paste", "Paste link", "As", "Display as icon", "Result"]),
 ("Options", lambda: win.run("options"), ["General", "Display", "Proofing", "Save", "Language", "Accessibility", "Advanced", "Customize Ribbon", "Quick Access Toolbar", "Add-ins", "Trust Center", "User name", "Initials", "AutoCorrect Options", "Save AutoRecover information every", "Default local file location", "Show text animation" ]),
 ("AutoCorrect", lambda: importlib.import_module("folio.options").autocorrect_dialog(win), ["AutoCorrect", "Math AutoCorrect", "AutoFormat As You Type", "AutoFormat", "Actions", "Show AutoCorrect Options buttons", "Correct TWo INitial CApitals", "Capitalize first letter of sentences", "Capitalize first letter of table cells", "Capitalize names of days", "Correct accidental usage of cAPS LOCK key", "Replace text as you type", "Exceptions", "Automatic bulleted lists", "Automatic numbered lists", "Border lines", "Built-in Heading styles", "Tables", "Ordinals (1st) with superscript", "Fractions (1/2) with fraction character", "Hyphens (--) with dash", "Internet and network paths with hyperlinks", "Format beginning of list item like the one before it", "Set left- and first-indent with tabs and backspaces", "Define styles based on your formatting"]),
 ("Envelopes", lambda: importlib.import_module("folio.dlg_mail").envelopes(win), ["Envelopes", "Labels", "Delivery address", "Return address", "Omit", "Preview", "Feed", "Print", "Add to Document", "Options", "E-postage"]),
 ("Labels", lambda: importlib.import_module("folio.dlg_mail").labels(win), ["Address", "Use return address", "Print", "Full page of the same label", "Single label", "Row", "Column", "Label", "Options", "New Document"]),
 ("Manage Sources", lambda: importlib.import_module("folio.dlg_cite").manage_sources(win), ["Master List", "Current List", "Copy", "Delete", "Edit", "New", "Preview", "Sort by", "Search", "Browse"]),
]
RESULTS_D = []
def run_spec(spec):
    title, opener, want = spec
    before = set(id(d) for d in dialogs_open())
    GLib.idle_add(lambda: (opener(), False)[1])
    yield 1.5
    new = [d for d in dialogs_open() if id(d) not in before]
    if not new:
        check("%s dialog opens" % title, False, [d.get_title() for d in dialogs_open()])
        return
    d = new[-1]
    t = texts_of(d).lower()
    open("/tmp/w8_texts.txt", "a").write("== %s\n%s\n" % (title, t))
    missing = [w for w in want if w.lower().replace("…", "") not in t]
    check("%s dialog complete" % title, not missing, "missing: %s" % missing)
    note("%s title" % title, d.get_title())
    shot("w8_" + title.replace(" ", "_"))
    close_dialogs(); yield 0.6
    for d2 in dialogs_open():
        try: d2.destroy()
        except Exception: pass
    yield 0.3
def dlgs():
    fresh(); yield 0.3
    T("Some text in the document to work with."); yield 0.4
    K("ctrl+a"); yield 0.3
    K("ctrl+c"); yield 0.3     # something on the clipboard for Paste Special
    for spec in SPECS:
        yield from run_spec(spec)
        focus()
run_scenarios(dlgs)
