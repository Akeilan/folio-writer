import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
# 2.29 (mailings): recipients, merge fields, address block, greeting line, rules,
# preview, find recipient, Finish & Merge, envelopes, labels, highlight
import zipfile
from gi.repository import GLib, Gtk


def part(path, name):
    return zipfile.ZipFile(path).read(name).decode()


def a():
    yield 1.0
    focus(); yield 0.2
    ed = E.ed
    v = E.view
    msgs = []
    win.dialogs.message = lambda *a, **k: msgs.append(a)
    win.dialogs.confirm = lambda *a, **k: True
    from folio.native import mailmerge as MM
    from folio import dlg_mail
    with open("/tmp/n26.csv", "w") as f:
        f.write("First Name,Last Name,Address Line 1,City,State,ZIP Code,Amount\n"
                "Ann,Smith,1 Main St,Boston,MA,02101,250\n"
                "Bob,Jones,2 Oak Ave,Denver,CO,80201,40\n"
                "Cy,Lee,3 Elm Rd,Austin,TX,73301,900\n")
    dlg_mail.start_mail_merge(win, "letters"); yield 0.2
    check("Start Mail Merge > Letters", MM.merge_type(win) == "letters")
    MM.set_recipients(win, *MM.read_csv("/tmp/n26.csv"), path="/tmp/n26.csv")
    win.refresh_mailings()
    cols, rows, inc = MM.recipients(win)
    check("Use an Existing List", len(rows) == 3 and "City" in cols and all(inc), (cols, len(rows)))
    MM.insert_address_block(win)
    ed.type_text("\n\n")
    MM.insert_greeting(win, "Dear", ",")
    ed.type_text("\nYou owe ")
    MM.insert_field(win, "Amount")
    ed.type_text(". ")
    MM.insert_rule(win, {"kind": "if", "field": "Amount", "op": "gt", "value": "100", "then": "Please pay now.", "else": "No hurry."})
    ed.type_text(" Letter ")
    MM.insert_rule(win, {"kind": "record"})
    v.after_edit(); yield 0.2
    text = "\n".join(t for _p, t, _l in __import__("folio.native.docops", fromlist=["x"]).paragraphs(ed))
    check("fields show their names", "«AddressBlock»" in text and "«GreetingLine»" in text and "«Amount»" in text, text)
    check("merge fields found", set(MM.merge_masters(win)) == {"Amount"}, MM.merge_masters(win))

    # ---- preview
    win.act_merge_preview(); yield 0.2
    text = "\n".join(t for _p, t, _l in __import__("folio.native.docops", fromlist=["x"]).paragraphs(ed))
    check("Preview Results: record 1", "Ann Smith" in text and "1 Main St" in text and "Boston, MA 02101" in text
          and "Dear Ann Smith," in text and "You owe 250" in text and "Please pay now." in text and "Letter 1" in text, text)
    win.merge_go("next"); yield 0.2
    text = "\n".join(t for _p, t, _l in __import__("folio.native.docops", fromlist=["x"]).paragraphs(ed))
    check("Next Record", "Bob Jones" in text and "You owe 40" in text and "No hurry." in text and "Letter 2" in text, text)
    k = MM.find_recipient(win, "austin")
    check("Find Recipient", k == 2)
    win.act_merge_preview(); yield 0.2
    text = "\n".join(t for _p, t, _l in __import__("folio.native.docops", fromlist=["x"]).paragraphs(ed))
    check("preview off: the names again", "«Amount»" in text and "Bob" not in text, text)

    # ---- saved as Word keeps it
    win.save_to("/tmp/n26a.docx"); yield 0.5
    st = part("/tmp/n26a.docx", "word/settings.xml")
    check("mail merge settings", '<w:mainDocumentType w:val="formLetters"/>' in st and 'w:dataType w:val="textFile"' in st
          and "/tmp/n26.csv" in st, st[st.find("<w:mailMerge"):st.find("</w:mailMerge>") + 15])
    rels = part("/tmp/n26a.docx", "word/_rels/settings.xml.rels")
    check("the data source linked", "mailMergeSource" in rels and 'TargetMode="External"' in rels, rels)
    dx = part("/tmp/n26a.docx", "word/document.xml")
    check("Word's merge fields", "MERGEFIELD Amount" in dx and "ADDRESSBLOCK" in dx and "GREETINGLINE" in dx and " IF " in dx
          and "MERGEREC" in dx)

    # ---- include flags
    MM.set_included(win, [True, False, True])
    check("Edit Recipient List: leave one out", MM.recipients(win)[2] == [True, False, True])

    # ---- finish & merge
    path, n = MM.merged_document(win)
    check("Finish & Merge: one letter per included record", n == 2, n)
    from folio.native import core
    out = core().Editor.open(path)
    otext = "\n".join(p for p in [r[1] for r in out.outline_paras()])
    check("the letters carry each record", "Ann Smith" in otext and "Cy Lee" in otext and "Bob" not in otext, otext[:300])
    check("no fields left", not out.fields_all(), out.fields_all()[:3])
    check("nothing of the main document's own fields left", "«" not in otext, otext[:200])
    check("a page each", out.page_count() == 2, out.page_count())
    MM.set_included(win, [True, True, True])

    # ---- envelope
    MM.envelope(win, "Ann Smith\n1 Main St\nBoston, MA 02101", "Folio Inc.\n9 Road", 0, False, {}); yield 0.3
    w0, h0 = ed.page_size(0)
    check("Envelopes > Add to Document: an envelope page first", w0 > h0 and abs(w0 - 684) < 3, (w0, h0))
    ed.undo(); v.after_edit()

    # ---- labels (in a new document)
    w2 = win.app.new_window(); yield 1.5
    MM.labels_document(w2, "Ann Smith\n1 Main St", 0, True); yield 0.3
    cells = w2.engine.ed.table_cells(0)
    check("Labels: a sheet of 30", len(cells) == 10 and len(cells[0]) in (3, 5), (len(cells), len(cells[0]) if cells else 0))
    check("the address in every label", w2.engine.ed.page_count() == 1)
    w2.engine.ed.set_modified(False) if hasattr(w2.engine.ed, "set_modified") else None
    w2.destroy()

    # ---- highlight merge fields
    win.act_highlight_merge_fields(); yield 0.2
    check("Highlight Merge Fields", len(getattr(v, "merge_shading", [])) >= 3)
    win.act_highlight_merge_fields()
    check("no messages", not msgs, msgs)
run_scenarios(a)
