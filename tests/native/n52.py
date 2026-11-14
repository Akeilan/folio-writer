# W5-11: e-mail goes to the computer's own mail program, not to a discontinued app.
import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d)))
exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
import json
import tempfile
from folio import dlg_mail
from folio.native import mailmerge

MSG = []
win.dialogs.message = lambda *a, **k: MSG.append(str(a[0])[:200] if a else "")
win.dialogs.confirm = lambda *a, **k: True

def a():
    yield 0.4
    check("Page looks for the computer's mail program", hasattr(mailmerge, "mail_program"))
    note("mail program here", mailmerge.mail_program())
    # nothing anywhere should send people to the discontinued app
    import folio
    root = os.path.dirname(folio.__file__)
    bad = []
    for f in sorted(os.listdir(root)):
        if not f.endswith(".py"):
            continue
        for i, line in enumerate(open(os.path.join(root, f), encoding="utf-8"), 1):
            tells = "install" in line.lower() or "comes with" in line.lower()
            if "Folio Post" in line and tells and ("message(" in line or "flash(" in line):
                bad.append("%s:%d" % (f, i))
    check("no message tells the user to install Folio Post", not bad, bad)

def opens_mail():
    yield 0.3
    d = tempfile.mkdtemp(prefix="n52_")
    att = os.path.join(d, "Letter.docx")
    E.ed.save(att)
    job = os.path.join(d, "merge.json")
    with open(job, "w", encoding="utf-8") as fh:
        json.dump({"subject": "Our offer", "format": "attachment", "messages": [
            {"to": "a@example.org", "subject": "Our offer", "text": "Hello", "attachments": [att]},
            {"to": "b@example.org", "subject": "Our offer", "text": "Hello", "attachments": [att]}]}, fh)
    calls = []
    fake = os.path.join(d, "xdg-email")
    with open(fake, "w") as fh:
        fh.write("#!/bin/sh\necho \"$@\" >> %s/calls.txt\n" % d)
    os.chmod(fake, 0o755)
    mailmerge.mail_program = lambda: fake
    mailmerge.post_program = lambda: None
    del MSG[:]
    dlg_mail._launch_desktop_mail(win, job, d, 2)
    yield 1.2
    try:
        calls = open(os.path.join(d, "calls.txt")).read().strip().splitlines()
    except OSError:
        calls = []
    check("each recipient is opened in the mail program", len(calls) == 2, (calls, MSG))
    check("with the address", all("@example.org" in c for c in calls), calls)
    check("the subject", all("Our offer" in c for c in calls), calls)
    check("and the merged document attached", all("Letter.docx" in c for c in calls), calls)
    check("nothing is sent without the user pressing Send",
          "press Send" in win.status_text() if hasattr(win, "status_text") else True)
    check("no error was shown", not MSG, MSG)

def no_mail_program():
    yield 0.3
    mailmerge.mail_program = lambda: None
    mailmerge.post_program = lambda: None
    del MSG[:]
    ok = dlg_mail._need_mail(win, "Sending e-mail")
    check("without a mail program it says so plainly", not ok and MSG, MSG)
    check("and names what to do", MSG and "set up" in MSG[0].lower() and "Folio Post" not in MSG[0], MSG)
run_scenarios(a, opens_mail, no_mail_program)
