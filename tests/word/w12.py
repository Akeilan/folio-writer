exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
def items(c):
    m = getattr(c, "menu", None)
    if callable(m):
        try:
            m = m()
        except Exception as e:
            return ["<callable:%s>" % type(e).__name__]
        if isinstance(m, Gtk.Widget):
            out = []
            for w in find_widget(m, lambda x: isinstance(x, (Gtk.Label,))):
                out.append(w.get_text())
            return out
    out = []
    for it in (m or []):
        if not it or isinstance(it, Gtk.Widget):
            continue
        out.append(it[1] if it[0] == "#" and len(it) > 1 and isinstance(it[1], str) else it[0])
        # a submenu's items count too
        if len(it) > 1 and isinstance(it[1], list):
            out += [x[0] for x in it[1] if x and isinstance(x, (list, tuple))]
    return out
WANT = {
 ("Picture Format", "Wrap Text"): ["In Line with Text", "Square", "Tight", "Through", "Top and Bottom", "Behind Text", "In Front of Text", "Edit Wrap Points", "Move with Text", "Fix Position on Page", "More Layout Options"],
 ("Picture Format", "Crop"): ["Crop", "Crop to Shape", "Aspect Ratio", "Fill", "Fit"],
 ("Picture Format", "Picture Effects"): ["Shadow", "Reflection", "Glow", "Soft Edges", "Bevel", "3-D Rotation"],
 ("Picture Format", "Position"): ["In Line with Text", "With Text Wrapping", "More Layout Options"],
 ("Shape Format", "Shape Effects"): ["Shadow", "Reflection", "Glow", "Soft Edges", "Bevel", "3-D Rotation"],
 ("Home", "Change Case"): ["Sentence case.", "lowercase", "UPPERCASE", "Capitalize Each Word", "tOGGLE cASE"],
 ("Home", "Select"): ["Select All", "Select Objects", "Select All Text With Similar Formatting", "Selection Pane"],
 ("Home", "Find"): ["Find", "Advanced Find", "Go To"],
 ("Home", "Borders"): ["Bottom Border", "Top Border", "Left Border", "Right Border", "No Border", "All Borders", "Outside Borders", "Inside Borders", "Inside Horizontal Border", "Inside Vertical Border", "Diagonal Down Border", "Diagonal Up Border", "Horizontal Line", "Draw Table", "View Gridlines", "Borders and Shading"],
 ("Layout", "Breaks"): ["Page", "Column", "Text Wrapping", "Next Page", "Continuous", "Even Page", "Odd Page"],
 ("Layout", "Hyphenation"): ["None", "Automatic", "Manual", "Hyphenation Options"],
 ("Layout", "Line Numbers"): ["None", "Continuous", "Restart Each Page", "Restart Each Section", "Suppress for Current Paragraph", "Line Numbering Options"],
 ("Layout", "Size"): ["Letter", "Legal", "A4", "More Paper Sizes"],
 ("Layout", "Margins"): ["Normal", "Narrow", "Moderate", "Wide", "Mirrored", "Custom Margins"],
 ("References", "Insert Citation"): ["Add New Source", "Add New Placeholder"],
 ("References", "Bibliography"): ["Bibliography", "References", "Works Cited", "Insert Bibliography", "Save Selection to Bibliography Gallery"],
 ("References", "Add Text"): ["Do Not Show in Table of Contents", "Level 1", "Level 2", "Level 3"],
 ("References", "Insert Footnote"): [],
 ("Review", "Delete"): ["Delete", "Delete All Comments Shown", "Delete All Comments in Document"],
 ("Review", "Track Changes"): ["For Everyone", "Just Mine", "Lock Tracking"],
 ("Review", "Restrict Editing"): [],
 ("View", "Macros"): ["View Macros", "Record Macro", "Pause Recording"],
 ("Insert", "Header"): ["Blank", "Blank (Three Columns)", "Edit Header", "Remove Header"],
 ("Insert", "Footer"): ["Blank", "Blank (Three Columns)", "Edit Footer", "Remove Footer"],
 ("Insert", "Shapes"): ["Lines", "Rectangles", "Basic Shapes", "Block Arrows", "Equation Shapes", "Flowchart", "Stars and Banners", "Callouts", "New Drawing Canvas"],
 ("Insert", "Symbol"): ["More Symbols"],
 ("Insert", "Text Box"): ["Simple Text Box", "Draw Text Box", "Save Selection to Text Box Gallery"],
 ("Insert", "Screenshot"): ["Screen Clipping"],
 ("Insert", "Object"): ["Object", "Text from File"],
 ("Mailings", "Start Mail Merge"): ["Letters", "E-mail Messages", "Envelopes", "Labels", "Directory", "Normal Word Document", "Step-by-Step Mail Merge Wizard"],
 ("Mailings", "Select Recipients"): ["Type a New List", "Use an Existing List", "Choose from Outlook Contacts"],
 ("Mailings", "Finish & Merge"): ["Edit Individual Documents", "Print Documents", "Send Email Messages"],
 ("Design", "Paragraph Spacing"): ["No Paragraph Space", "Compact", "Tight", "Open", "Relaxed", "Double", "Custom Paragraph Spacing"],
 ("Design", "Page Color"): ["No Color", "More Colors", "Fill Effects"],
 ("Draw", "Pen"): [],
}
def d():
    fresh(); yield 0.3
    for (tab, lab), want in WANT.items():
        c = find_control(tab, lab)
        if c is None:
            check("%s > %s exists" % (tab, lab), False)
            continue
        got = [ (g or "").replace("_", "").replace("\n", " ") for g in items(c)]
        flat = " | ".join(got).lower()
        missing = [w for w in want if w.lower() not in flat]
        check("%s > %s menu complete" % (tab, lab), not missing, "missing %s ; has %s" % (missing, got[:25]))
    yield 0.2
run_scenarios(d)
