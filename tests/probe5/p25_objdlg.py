# Effect walk: every ribbon control run with text selected. Records whether the document changed,
# whether Undo brings it back exactly, and whether Redo reapplies it.
import os, sys, zipfile, hashlib, traceback, time
os.environ["WALK_OUT"] = "/tmp/p5out/p1_walk_unused.txt"
_src = open(os.path.join(os.environ["FOLIO_WRITER_TESTS"], "native_command_walk.py")).read()
exec(_src.split("\ndef walk(")[0])
RES = open("/tmp/p5out/p25_objdlg.tsv", "w")
ed = win.engine.ed
import traceback as _tb
from folio.native import uno_model as _um2, uno_props as _up2
MISS = {}
CURL = {"l": ""}
def _wrap(cls):
    g = cls.__getattr__
    def ga(self, k):
        try:
            return g(self, k)
        except AttributeError:
            if not k.startswith("__"):
                fr = [f for f in _tb.extract_stack()[:-1] if "/folio/" in f.filename and "uno_" not in f.filename]
                where = "%s:%d %s" % (os.path.basename(fr[-1].filename), fr[-1].lineno, fr[-1].name) if fr else "?"
                MISS.setdefault((cls.__name__, k, where), set()).add(CURL["l"])
            raise
    cls.__getattr__ = ga
for _c in (_um2.NativeModel, _up2.CursorProps, _up2.NativeModel, _um2.NativeStyle):
    _wrap(_c)
DLG = []
def _ok(self, *a):
    UI["n"] += 1
    t = type(self).__name__ + ":" + (self.get_title() or "")
    DLG.append(t)
    if DLG.count(t) > 2:
        return Gtk.ResponseType.CANCEL
    if isinstance(self, (Gtk.FileChooserDialog, Gtk.FileChooserNative)) or "Print" in t:
        return Gtk.ResponseType.CANCEL
    for r in (Gtk.ResponseType.OK, Gtk.ResponseType.ACCEPT, Gtk.ResponseType.APPLY, Gtk.ResponseType.YES):
        if self.get_widget_for_response(r) is not None:
            return r
    return Gtk.ResponseType.OK
Gtk.Dialog.run = _ok

def fp():
    p = "/tmp/p5out/_fp25.docx"
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

CTX = {"tab": None}
_setup0 = setup
def setup():
    _setup0()
    e = win.engine.ed
    t = CTX["tab"]
    if t in ("Table Design", "Table Layout"):
        e.move_caret("doc_end", False); e.type_text("\n")
        e.insert_table(3, 3)
        for i in range(9):
            e.type_text("c%d" % i)
            if i < 8: e.cell_step(False)
        # caret to the middle cell
        e.cell_step(True); e.cell_step(True); e.cell_step(True); e.cell_step(True)
    elif t == "Header & Footer":
        win.run("edit-header") if False else e.edit_header_footer(0, False)
        e.type_text("Head")
    elif t == "Picture Format":
        e.move_caret("doc_end", False); e.type_text("\n")
        e.insert_picture(os.path.join(os.environ["FOLIO_SHARE"], "icons", "folio-page-128.png"))
    elif t == "Shape Format":
        e.insert_shape("rect", 0, 300, 300, 100, 60, "Rectangle", False)
    elif t == "Equation":
        win.engine.command(".uno:InsertObjectStarMath") if False else None
        e.move_caret("doc_end", False); e.type_text("\n")
        R_eq()
    win.engine.view.after_edit() if hasattr(win.engine.view, "after_edit") else None
    try:
        win.update_object_tabs()
    except Exception:
        pass
    pump(0.1)

def R_eq():
    for tab, label, fn in ALL:
        if label.startswith("Equation (Alt+=)") and " > " not in label:
            fn(); pump(0.2); win.engine.ed.type_text("x^2+y"); return

ALL = items_of()
TABS = ('Table Design', 'Table Layout', 'Header & Footer', 'Picture Format', 'Shape Format')
itemsX = items_of(exclude=("Picture Format", "Shape Format", "Table Design", "Table Layout", "Chart Design",
                          "SmartArt Design", "Equation", "Header & Footer", "Background Removal", "File"))
SKIPX = SKIP + ("immersive", "new window", "restrict", "protect", "compare", "combine", "mail merge wizard",
                "finish", "send e", "split", "arrange all", "switch windows", "full screen", "focus")
n = 0
for tab, label, fn in [x for x in ALL if x[0] in TABS]:
    if any(s in label.lower() for s in SKIPX):
        continue
    n += 1
    try:
        CTX["tab"] = tab
        CURL['l'] = tab + ' | ' + label
        setup()
        base_undo = len(ed.undo_names()) if hasattr(ed, "undo_names") else 0
        f0 = fp()
        del DLG[:]; n0 = len(ERR); flag["ny"] = False; UI["n"] = 0
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
            if undo == "ok":
                k = 0
                while ed.can_redo() and k < steps:
                    ed.redo(); k += 1
                redo = "ok" if fp() == f1 else "BROKEN"
        res = "ERROR" if err else ("NOT_YET" if flag["ny"] else ("CHANGED" if changed else ("UI" if UI["n"] else "SAME")))
        RES.write("\t".join([tab, label, res, undo, redo, "%.2f" % dt, ";".join(DLG)[:80], err]) + "\n") if DLG else None; RES.flush()
        for w in Gtk.Window.list_toplevels():
            if w is not win and w.get_visible() and w.get_transient_for() is win:
                w.hide()
    except Exception as e:
        RES.write("\t".join([tab, label, "HARNESS", "-", "-", "0", repr(e)[:200] + traceback.format_exc()[-200:].replace("\n", " | ")]) + "\n"); RES.flush()
RES.write("DONE %d\n" % n); RES.close()
with open("/tmp/p5out/p25_miss.tsv", "w") as f:
    for (c, k, where), labs in sorted(MISS.items(), key=lambda kv: kv[0][2]):
        f.write("%s.%s\t%s\t%d\t%s\n" % (c, k, where, len(labs), " ;; ".join(sorted(labs))[:300]))
os._exit(0)
