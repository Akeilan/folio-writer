exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
# 2.31: File > Share > Email: the document or a PDF attached to a new message (M-12)
import os
import shutil
import stat
import subprocess
import zipfile

CALLS = []
_popen = subprocess.Popen


class FakePopen:
    def __init__(self, args, *a, **k):
        CALLS.append(list(args))




def send(pdf):
    subprocess.Popen = FakePopen
    try:
        return win.send_attachment(pdf)
    finally:
        subprocess.Popen = _popen
_which = shutil.which
WHICH = {"folio-post": "/usr/bin/folio-post"}
shutil.which = lambda name, *a, **k: WHICH.get(name, None) if name in ("folio-post", "xdg-email") else _which(name, *a, **k)
MSG = []
win.dialogs.message = lambda text, *a, **k: MSG.append(text)


def a():
    yield 1.0
    focus(); fresh(); yield 0.2
    T("Shared text"); yield 0.3
    was = E.ed.modified
    # ---- the Share page in File
    bs = win.backstage
    bs.open("share"); yield 0.6
    check("File > Share page", bs.current == "share" and "share" in bs.nav_buttons, bs.current)
    shot("n35_share")
    bs.close(); yield 0.3
    p = send(False); yield 0.5
    check("attachment made", p and p.endswith(".docx") and zipfile.is_zipfile(p), p)
    check("handed to Folio Post", CALLS and CALLS[-1][:2] == ["/usr/bin/folio-post", "--attach"] and CALLS[-1][2] == p, CALLS)
    check("document still unsaved", E.ed.modified == was, (E.ed.modified, was))
    p2 = send(True); yield 0.8
    check("PDF attachment", p2 and p2.endswith(".pdf") and open(p2, "rb").read(4) == b"%PDF", p2)
    # without Folio Post: the desktop's mail app
    WHICH.clear(); WHICH["xdg-email"] = "/usr/bin/xdg-email"
    p3 = send(False); yield 0.5
    check("xdg-email when Folio Post isn't there", CALLS[-1][0] == "xdg-email" and "--attach" in CALLS[-1], CALLS[-1])
    WHICH.clear()
    p4 = send(False); yield 0.3
    check("no mail app: says so", p4 is None and any("mail app" in m for m in MSG), MSG)
    E.ed.mark_saved()


run_scenarios(a)
