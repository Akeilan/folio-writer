import os as _o; TESTS = _o.environ["FOLIO_WRITER_TESTS"]; exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read()); exec(open("/tmp/p5/probes/ph.py").read())
import subprocess
MSG = []
win.dialogs.message = lambda *a, **k: MSG.append(str(a[0])[:140] if a else "")
def a():
    yield 0.5
    if os.path.exists("/tmp/p5out/lp_calls.txt"): os.remove("/tmp/p5out/lp_calls.txt")
    win.open_file("/tmp/corpus/sections.docx"); yield 2.0
    win.act_backstage_print(); yield 2.5
    shot("print_page")
    bs = win.backstage
    combos = find_widget(bs, lambda w: isinstance(w, Gtk.ComboBoxText))
    note("combos", [(c.get_active_id(), c.get_active_text()) for c in combos])
    btns = [b for b in find_widget(bs, lambda w: isinstance(w, Gtk.Button)) if (b.get_label() or "").strip() == "Print" or "Print" in " ".join(l.get_text() for l in find_widget(b, lambda x: isinstance(x, Gtk.Label)))]
    note("print buttons", [b.get_label() for b in btns][:5])
    note("preview pages label", [l.get_text() for l in find_widget(bs, lambda w: isinstance(w, Gtk.Label)) if l.get_text().startswith("of ")])
    if btns:
        btns[-1].clicked(); yield 1.5
    calls = open("/tmp/p5out/lp_calls.txt").read() if os.path.exists("/tmp/p5out/lp_calls.txt") else ""
    note("lp called with", calls.strip())
    check("Print hands the document to the printer", "Office_Laser" in calls, (calls, MSG))
    if os.path.exists("/tmp/p5out/lp_last.pdf"):
        info = subprocess.run(["pdfinfo", "-l", "9", "/tmp/p5out/lp_last.pdf"], capture_output=True, text=True).stdout
        sizes = re.findall(r"Page\s+(\d+) size:\s+([\d.]+) x ([\d.]+)", info)
        note("pages sent", sizes)
        check("all 6 pages are sent, landscape and A5 ones at their own size", len(sizes) == 6 and len(set((a, b) for _n, a, b in sizes)) == 3, sizes)
    note("messages", MSG)
    note("modified after printing", ed().modified)
import re
run_scenarios(a)
