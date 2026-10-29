import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
# 2.32 (W3-02, W3-03): mail merge to e-mail through Folio Post (--send-merge), and recipients
# from Folio Post's contacts (--list-contacts). A stand-in folio-post records what it is given.
import json
import os
import stat
import zipfile
from gi.repository import GLib, Gtk

BIN = "/tmp/n37bin"
os.makedirs(BIN, exist_ok=True)
with open(BIN + "/folio-post", "w") as f:
    f.write('''#!/usr/bin/env python3
import json, shutil, sys
a = sys.argv[1:]
if a[:1] == ["--send-merge"]:
    shutil.copy(a[1], "/tmp/n37_job.json")
    job = json.load(open(a[1]))
    print(json.dumps({"sent": len(job["messages"]), "failed": []}))
    sys.exit(0)
if a[:1] == ["--list-contacts"]:
    print(json.dumps([
        {"name": "Ann Smith", "email": "ann@example.org", "company": "Acme", "phone": "1", "groups": ["Team"]},
        {"name": "Bob Jones", "email": "bob@example.org", "company": "", "phone": "", "groups": []},
        {"name": "Cy", "email": "cy@example.org", "company": "Lee & Co", "phone": "", "groups": ["Team"]}]))
    sys.exit(0)
sys.exit(2)
''')
os.chmod(BIN + "/folio-post", 0o755)
os.environ["PATH"] = BIN + ":" + os.environ.get("PATH", "")


def a():
    yield 1.0
    focus(); fresh(); yield 0.2
    ed = E.ed
    msgs = []
    win.dialogs.message = lambda *a, **k: msgs.append(a)
    from folio.native import mailmerge as MM
    from folio import dlg_mail
    with open("/tmp/n37.csv", "w") as f:
        f.write("First Name,Last Name,E-mail Address,Amount\n"
                "Ann,Smith,ann@example.org,250\n"
                "Bob,Jones,,40\n"
                "Cy,Lee,cy@example.org,900\n")
    check("Folio Post found", MM.post_program() == BIN + "/folio-post", MM.post_program())
    dlg_mail.start_email(win); yield 0.4
    check("Start Mail Merge > E-mail Messages", MM.merge_type(win) == "email", MM.merge_type(win))
    MM.set_recipients(win, *MM.read_csv("/tmp/n37.csv"), path="/tmp/n37.csv")
    win.refresh_mailings()
    check("the e-mail column is found", MM.email_columns(win)[0] == "E-mail Address", MM.email_columns(win))
    ed.type_text("Dear ")
    MM.insert_field(win, "First Name")
    ed.type_text(",\nYou owe ")
    MM.insert_field(win, "Amount")
    ed.type_text(" dollars."); yield 0.3
    job, tmpd, n = MM.email_messages(win, "E-mail Address", "Your bill", "html")
    data = json.load(open(job))
    m = data["messages"]
    check("one message per record with an address (Bob has none)", n == 2 and [x["to"] for x in m] == ["ann@example.org", "cy@example.org"], [x["to"] for x in m])
    check("subject on every message", data["subject"] == "Your bill" and all(x["subject"] == "Your bill" for x in m))
    check("HTML body merged", "Dear Ann" in m[0]["html"] and "250" in m[0]["html"] and "Dear Cy" in m[1]["html"], m[0]["html"][-400:])
    check("plain-text part too", "You owe 900 dollars." in m[1]["text"], m[1]["text"])
    check("no merge-field placeholders left", not any("«" in x["html"] + x["text"] for x in m), m[0]["text"])
    job2, tmpd2, n2 = MM.email_messages(win, "E-mail Address", "Your bill", "text")
    m2 = json.load(open(job2))["messages"]
    check("plain text format", "html" not in m2[0] and m2[0]["text"].startswith("Dear Ann,"), m2[0])
    job3, tmpd3, n3 = MM.email_messages(win, "E-mail Address", "Bill", "attachment", attachment_name="Bill.docx")
    m3 = json.load(open(job3))["messages"]
    att = m3[1]["attachments"][0]
    body = zipfile.ZipFile(att).read("word/document.xml").decode()
    check("attachment: the merged document", att.endswith("Bill.docx") and "Cy" in body and "MERGEFIELD" not in body, att)
    job4, tmpd4, n4 = MM.email_messages(win, "E-mail Address", "One", "html", which="range", first=3, last=3)
    check("From/To range", n4 == 1 and json.load(open(job4))["messages"][0]["to"] == "cy@example.org")
    # handed to Folio Post
    win.merge_mail_result = None
    dlg_mail._launch_post(win, job, tmpd, n)
    for _ in range(40):
        yield 0.2
        if win.merge_mail_result is not None:
            break
    got = json.load(open("/tmp/n37_job.json")) if os.path.exists("/tmp/n37_job.json") else {}
    check("folio-post --send-merge gets the job", len(got.get("messages", [])) == 2, got.keys())
    check("result read back", (win.merge_mail_result or {}).get("sent") == 2 and not os.path.exists(tmpd), win.merge_mail_result)
    # the ribbon no longer refuses these
    from folio import ribbon_defs
    src = open(ribbon_defs.__file__).read()
    check("no 'no e-mail connection' commands left", "DM.not_available(win" not in src)
    # ---- Choose from Outlook Contacts: Folio Post's contacts
    cs = MM.post_contacts()
    check("--list-contacts read", len(cs) == 3 and cs[0]["email"] == "ann@example.org", cs)
    orig_ask = dlg_mail.FDialog.ask

    def auto_ok(self):
        d, store, grp = win.post_contacts_dialog
        grp.set_active(1)  # "Team"
        return Gtk.ResponseType.OK
    dlg_mail.FDialog.ask = auto_ok
    try:
        dlg_mail.choose_post_contacts(win)
    finally:
        dlg_mail.FDialog.ask = orig_ask
    yield 0.3
    cols, rows, inc = MM.recipients(win)
    check("contacts become the recipient list (group Team: 2)", cols == MM.CONTACT_COLUMNS and len(rows) == 2, (cols, rows))
    check("names split", rows[0]["First Name"] == "Ann" and rows[0]["Last Name"] == "Smith" and rows[1]["First Name"] == "Cy" and rows[1]["Company Name"] == "Lee & Co", rows)
    # ---- without Folio Post: says it needs it
    os.environ["PATH"] = os.environ["PATH"].replace(BIN + ":", "")
    msgs.clear()
    real_find = MM.post_program
    MM.post_program = lambda *a, **k: None   # as if Post weren't installed (the test machines have it)
    try:
        dlg_mail.send_email(win)
    finally:
        MM.post_program = real_find
    check("without Post: needs Folio Post", any("Folio Post" in str(x) for x in msgs), msgs)
    ed.mark_saved()



run_scenarios(a)
