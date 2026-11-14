# Effect walk: every ribbon control run with text selected. Records whether the document changed,
# whether Undo brings it back exactly, and whether Redo reapplies it.
import os, sys, zipfile, hashlib, traceback, time
os.environ["WALK_OUT"] = "/tmp/p5out/p1_walk_unused.txt"
_src = open(os.path.join(os.environ["FOLIO_WRITER_TESTS"], "native_command_walk.py")).read()
exec(_src.split("\ndef walk(")[0])
RES = open("/tmp/p5out/p1b.tsv", "w")
WANT = set(l.split("\t")[1] for l in open("/tmp/p5out/p1_effect.tsv") if "BROKEN" in l)
ed = win.engine.ed

def parts():
    p = "/tmp/p5out/_fpb_%d.docx" % os.getpid()
    ed.save(p)
    with zipfile.ZipFile(p) as z:
        return {n: z.read(n) for n in z.namelist() if not n.startswith("docProps/")}

import difflib, re
def explain(a, b):
    out = []
    for n in sorted(set(a) | set(b)):
        if n not in a: out.append("+" + n); continue
        if n not in b: out.append("-" + n); continue
        if a[n] != b[n]:
            x = re.sub(rb">\s*<", b">\n<", a[n]).decode("utf8", "replace").split("\n")
            y = re.sub(rb">\s*<", b">\n<", b[n]).decode("utf8", "replace").split("\n")
            d = [l for l in difflib.unified_diff(x, y, lineterm="", n=0) if l[:1] in "+-" and l[:3] not in ("+++", "---")]
            out.append("~%s: %s" % (n, " ".join(d)[:420]))
    return " || ".join(out)

def fp():
    p = "/tmp/p5out/_fp_%d.docx" % os.getpid()
    try:
        ed.save(p)
    except Exception as e:
        return "SAVEFAIL %r" % (e,)
    h = hashlib.sha1()
    with zipfile.ZipFile(p) as z:
        for n in sorted(z.namelist()):
            if n.startswith("docProps/"):
                continue
            h.update(n.encode()); h.update(z.read(n))
    return h.hexdigest()

def setup():
    e = win.engine.ed
    try:
        if e.story() != "body":
            e.edit_notes(None)
    except Exception:
        pass
    try:
        e.leave_textbox()
    except Exception:
        pass
    e.deselect_object()
    while e.can_undo():
        e.undo()
    e.select_all(); e.delete(True, False)
    e.type_text("Alpha beta gamma delta.\nSecond paragraph with several words in it.\nThird and last paragraph.")
    win.engine.view.after_edit() if hasattr(win.engine.view, "after_edit") else None
    pump(0.05)
    e.select_range(1, 7, 1, 21)      # "paragraph with"
    pump(0.05)

items = items_of(exclude=("Picture Format", "Shape Format", "Table Design", "Table Layout", "Chart Design",
                          "SmartArt Design", "Equation", "Header & Footer", "Background Removal", "File"))
SKIPX = SKIP + ("immersive", "new window", "restrict", "protect", "compare", "combine", "mail merge wizard",
                "finish", "send e", "split", "arrange all", "switch windows", "full screen", "focus")
n = 0
for tab, label, fn in items:
    if label not in WANT:
        continue
    n += 1
    try:
        setup()
        base_undo = len(ed.undo_names()) if hasattr(ed, "undo_names") else 0
        f0 = fp(); P0 = parts()
        n0 = len(ERR); flag["ny"] = False; UI["n"] = 0
        t0 = time.time()
        fn(); pump(0.08)
        dt = time.time() - t0
        err = ERR[-1].replace("\n", " | ")[-260:] if len(ERR) > n0 else ""
        f1 = fp()
        changed = f1 != f0
        undo = redo = "-"
        if changed:
            steps = 0
            while ed.can_undo() and len(ed.undo_names()) > base_undo and steps < 50:
                ed.undo(); steps += 1
            f2 = fp()
            undo = "ok" if f2 == f0 else ("BROKEN(steps=%d)" % steps)
            if undo != "ok":
                err = "story=%s names=%s :: %s" % (ed.story(), ed.undo_names()[-3:], explain(P0, parts()))
            if undo == "ok":
                k = 0
                while ed.can_redo() and k < steps:
                    ed.redo(); k += 1
                redo = "ok" if fp() == f1 else "BROKEN"
        res = "ERROR" if err else ("NOT_YET" if flag["ny"] else ("CHANGED" if changed else ("UI" if UI["n"] else "SAME")))
        RES.write("\t".join([tab, label, res, undo, redo, "%.2f" % dt, err]) + "\n"); RES.flush()
        for w in Gtk.Window.list_toplevels():
            if w is not win and w.get_visible() and w.get_transient_for() is win:
                w.hide()
    except Exception as e:
        RES.write("\t".join([tab, label, "HARNESS", "-", "-", "0", repr(e)[:200] + traceback.format_exc()[-200:].replace("\n", " | ")]) + "\n"); RES.flush()
RES.write("DONE %d\n" % n); RES.close()
os._exit(0)
