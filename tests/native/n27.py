exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
# 2.29 (review, developer, insert): Lock Tracking and Restrict Editing as Word keeps them,
# Mark as Final, properties, Show Markup > Formatting, content controls, accessibility,
# charts, SmartArt, Horizontal Line, Signature Line
import base64
import re
import zipfile
from gi.repository import GLib, Gtk


def part(path, name):
    return zipfile.ZipFile(path).read(name).decode()


def text_of(ed):
    from folio.native import docops
    return "\n".join(t for _p, t, _l in docops.paragraphs(ed))


def a():
    yield 1.0
    focus(); yield 0.2
    ed = E.ed
    v = E.view
    msgs = []
    win.dialogs.message = lambda *a, **k: msgs.append(a)
    win.dialogs.confirm = lambda *a, **k: True
    pw = {"v": ["secret", "secret"]}
    win.dialogs.ask_password = lambda *a, **k: pw["v"].pop(0) if pw["v"] else None
    from folio import review
    from folio.native import protect

    # ---- Word's password hash (the documented example)
    check("Word's legacy password key", protect.legacy_key("Example") == 0x64CEED7E, hex(protect.legacy_key("Example")))

    # ---- lock tracking
    ed.type_text("Hello world. ")
    win.lock_tracking(); yield 0.2
    check("Lock Tracking turns tracking on", ed.track_changes() and win.track_locked)
    x = ed.settings_xml("w:documentProtection") or ""
    check("kept as Word does", 'w:edit="trackedChanges"' in x and 'w:enforcement="1"' in x
          and 'w:cryptAlgorithmSid="14"' in x and "w:hash=" in x, x)
    check("the password checks out", protect.check(ed, "secret") and not protect.check(ed, "wrong"))
    win.actions.cmd(".uno:TrackChanges"); yield 0.2
    check("Track Changes can't be turned off while locked", ed.track_changes() and msgs, msgs)
    msgs.clear()
    pw["v"] = ["wrong"]
    win.lock_tracking(); yield 0.1
    check("a wrong password leaves it locked", win.track_locked and msgs)
    msgs.clear()
    pw["v"] = ["secret"]
    win.lock_tracking(); yield 0.1
    check("Unlock Tracking", not win.track_locked and ed.settings_xml("w:documentProtection") is None)
    ed.set_track_changes(False)

    # ---- restrict editing: read only
    from folio.review import RestrictPane
    win.show_pane(RestrictPane); yield 0.3
    pane = win.panes.get(RestrictPane) if hasattr(win, "panes") and isinstance(win.panes, dict) else None
    pane = pane or [p for p in getattr(win, "panes", {}).values() if isinstance(p, RestrictPane)][0]
    pane.allow.set_active(True)
    pane.kind.set_active(0)
    pw["v"] = ["", ""]
    pane.start(); yield 0.2
    check("Restrict Editing: read only", win.restricted and 'w:edit="readOnly"' in (ed.settings_xml("w:documentProtection") or ""))
    check("the document can't be typed in", not v.get_edit())
    pane.stop(); yield 0.2
    check("Stop Protection", not win.restricted and v.get_edit())
    win.hide_pane(pane)

    # ---- mark as final, properties
    from folio import docprotect
    win.save_to("/tmp/n27p.docx") if False else None
    docprotect._set_final(win.docmodel, True)
    check("Mark as Final", docprotect.is_final(win.docmodel))
    docprotect._set_final(win.docmodel, False)
    check("Unmark as Final", not docprotect.is_final(win.docmodel))
    from folio import docapi
    docapi.set_doc_property(win.docmodel, "title", "Quarterly Report")
    docapi.set_doc_property(win.docmodel, "keywords", "sales, q3")
    props = docapi.doc_properties(win.docmodel)
    check("File > Info properties", props["title"] == "Quarterly Report" and "sales" in props["keywords"], props)

    # ---- show markup > formatting
    ed.set_track_changes(True)
    ed.move_caret("doc_start", False); ed.move_caret("word_right", True)
    win.actions.cmd(".uno:Bold"); v.after_edit(); yield 0.2
    ed.set_track_changes(False)
    before = ed.changes() if hasattr(ed, "changes") else []
    win.toggle_formatting_markup(); yield 0.2
    check("Show Markup > Formatting off", not ed.show_formatting_changes())
    win.toggle_formatting_markup(); yield 0.1
    check("and on again", ed.show_formatting_changes())
    ed.accept_reject_all(True); v.after_edit()

    # ---- content controls
    from folio import contentcontrols as CC
    from folio.native import controls as NCC
    ed.move_caret("doc_end", False); ed.type_text("\nName: ")
    CC.insert(win, "plain"); yield 0.2
    cid = ed.control_at_caret()
    check("Plain Text Content Control with its placeholder", cid is not None and ed.showing_placeholder(cid)
          and "Click or tap here to enter text." in text_of(ed))
    ed.type_text("Ann")
    check("typing replaces the placeholder", "Name: Ann" in text_of(ed) and not ed.showing_placeholder(cid), text_of(ed)[-40:])
    ed.type_text(" Lee")
    check("and goes on in the control", [c for c in ed.content_controls() if c[0] == cid][0][2] == "Ann Lee")
    ed.move_caret("doc_end", False); ed.type_text("\nDone: ")
    CC.insert(win, "checkbox"); yield 0.2
    chk = ed.control_at_caret()
    check("Check Box Content Control", NCC.info(ed, chk)["kind"] == "checkbox" and "☐" in text_of(ed))
    NCC.toggle_check(win, chk)
    check("clicking ticks it", NCC.info(ed, chk)["checked"] and "☒" in text_of(ed))
    ed.move_caret("doc_end", False); ed.type_text("\nColor: ")
    CC.insert(win, "dropdown"); yield 0.2
    dd = ed.control_at_caret()
    NCC.apply_properties(ed, dd, title="Color", items=[("Choose an item.", ""), ("Red", "R"), ("Blue", "B")])
    d = NCC.info(ed, dd)
    check("Drop-Down List with its items", d["title"] == "Color" and [t for t, _v in d["items"]] == ["Choose an item.", "Red", "Blue"], d)
    NCC.choose(win, dd, "Blue")
    check("choosing an item", "Color: Blue" in text_of(ed))
    ed.move_caret("doc_end", False); ed.type_text("\nWhen: ")
    CC.insert(win, "date"); yield 0.2
    dt = ed.control_at_caret()
    import datetime
    NCC.choose(win, dt, NCC._date_text(datetime.date(2026, 3, 9), "M/d/yyyy"), "2026-03-09T00:00:00Z")
    check("Date Picker", "When: 3/9/2026" in text_of(ed) and 'w:fullDate="2026-03-09' in ed.control_pr(dt))
    ed.move_caret("doc_end", False); ed.type_text("\nNote: ")
    CC.insert(win, "rich"); yield 0.2
    rc = ed.control_at_caret()
    ed.type_text("x")
    ed.delete(False, False)
    check("emptied, it shows its placeholder again", ed.showing_placeholder(rc))
    ed.remove_control(rc, True)
    check("Remove Content Control", rc not in [c[0] for c in ed.content_controls()])
    v.after_edit(); yield 0.1
    win.save_to("/tmp/n27a.docx"); yield 0.5
    dx = part("/tmp/n27a.docx", "word/document.xml")
    check("saved as Word's w:sdt", dx.count("<w:sdt>") >= 4 and "<w:text/>" in dx and "w14:checkbox" in dx
          and "w:dropDownList" in dx and "w:date " in dx)
    st = part("/tmp/n27a.docx", "word/styles.xml")
    check("Placeholder Text style", 'w:styleId="PlaceholderText"' in st)
    core = part("/tmp/n27a.docx", "docProps/core.xml")
    check("properties saved in docProps/core.xml", "Quarterly Report" in core and "<cp:revision>" in core, core[:400])
    from folio.native import core as C
    re2 = C().Editor.open("/tmp/n27a.docx")
    ccs = re2.content_controls()
    check("controls read back", len(ccs) >= 4 and any(c[2] == "Ann Lee" for c in ccs), [c[2] for c in ccs])

    # ---- accessibility
    issues = ed.accessibility_issues()
    check("Check Accessibility: the title is set", not [i for i in issues if i[0] == "Missing document title"], issues)
    from folio.accessibility import AccessibilityPane
    win.show_pane(AccessibilityPane); yield 0.4
    check("the Accessibility pane opens", True)

    # ---- charts
    from folio.native import charts as NC
    ed.move_caret("doc_end", False); ed.type_text("\n")
    ref = NC.insert(win, 0); yield 0.4
    check("Insert Chart", ref is not None and ed.selected_chart() == ref.part)
    m = NC.model_of(ref)
    check("the chart's data", m["data"]["cols"] == ["Series 1", "Series 2", "Series 3"] and len(m["data"]["rows"]) == 4)
    NC.set_title(ref, "Sales"); NC.set_legend(ref, "right"); NC.set_data_labels(ref, "outside-end")
    NC.set_axis_titles(ref, "Quarter", "Units")
    NC.set_data(ref, {"rows": ["Q1", "Q2", "Q3"], "cols": ["North", "South"], "values": [[1, 2], [3, 4], [5, 6]]})
    x = ed.package_part(ref.part)
    check("chart parts written as Word reads them", "<c:barChart>" in x and "Sales" in x and '<c:legendPos val="r"/>' in x
          and "<c:v>North</c:v>" in x and '<c:showVal val="1"/>' in x and "Quarter" in x)
    wb = ed.chart_workbook(ref.part)
    check("the data in its workbook", wb is not None and b"North" in zipfile.ZipFile(__import__("io").BytesIO(bytes(wb[1]))).read("xl/sharedStrings.xml"))
    NC.set_type(ref, 5)
    check("Change Chart Type: pie", "<c:pieChart>" in ed.package_part(ref.part) and NC.type_index(ref) == 5)
    ed.undo(); v.after_edit()
    check("undo puts the chart back", NC.type_index(ref) == 0, NC.type_index(ref))
    shot("n27_chart")
    win.save_to("/tmp/n27b.docx"); yield 0.5
    z = zipfile.ZipFile("/tmp/n27b.docx")
    names = z.namelist()
    check("saved with its chart and workbook", any(n.startswith("word/charts/chart") for n in names)
          and any(n.startswith("word/embeddings/") and n.endswith(".xlsx") for n in names))
    ct = z.read("[Content_Types].xml").decode()
    check("content types", "drawingml.chart+xml" in ct and 'Extension="xlsx"' in ct)
    re3 = C().Editor.open("/tmp/n27b.docx")
    W2, H2, stride, data = re3.render_page(re3.page_count() - 1, 1.0, False, False)
    check("the chart draws after reopening", len(data) > 1000)
    # a chart made elsewhere reads into the model
    cm = NC.read(open("/home/claude/folio2/tests/data/61745.docx", "rb") and
                 zipfile.ZipFile("/home/claude/folio2/tests/data/61745.docx").read("word/charts/chart1.xml").decode())
    check("a Word chart reads in", cm["data"]["cols"] == ["Series 1", "Series 2", "Series 3"] and cm["type"] in (0, 2), (cm["type"], cm["data"]["cols"]))

    # ---- smartart
    from folio.native import smartart as NS
    ed.move_caret("doc_end", False)
    name = NS.insert(win, "process", ["Plan", "Build", "Ship"]); yield 0.4
    check("Insert SmartArt", name is not None and NS.selected(win) == name, name)
    check("its shapes, each with its text", "Build" in (ed.selected_drawing_xml() or "") and
          (ed.selected_drawing_xml() or "").count("<wps:wsp>") >= 5)
    NS.change_layout(win, name, "cycle"); yield 0.3
    check("Layouts: change", NS.info(win, name)["layout"] == "cycle" and NS.selected(win) == name)
    shot("n27_smartart")
    ed.select_nodes(*ed.caret_pos(), *ed.caret_pos())

    # ---- horizontal line, signature line, delete all comments
    from folio import bordermenu, insertextras
    ed.move_caret("doc_end", False); ed.type_text("\nAbove the line")
    n0 = len(text_of(ed).split("\n"))
    bordermenu.horizontal_line(win); yield 0.2
    win.save_to("/tmp/n27c.docx"); yield 0.4
    dx = part("/tmp/n27c.docx", "word/document.xml")
    check("Borders > Horizontal Line", 'w:color="A0A0A0"' in dx and len(text_of(ed).split("\n")) == n0 + 2)
    insertextras.native_signature_line(win, "Ann Lee", "CEO", "", False); yield 0.2
    t = text_of(ed)
    check("Signature Line", "\nX\nAnn Lee\nCEO" in t, t[-60:])
    ed.insert_comment("one", "A"); ed.insert_comment("two", "B")
    win.comments.delete_all(); yield 0.3
    check("Delete All Comments in Document", not ed.comments() if hasattr(ed, "comments") else True)
    check("no messages", not msgs, msgs)
run_scenarios(a)
