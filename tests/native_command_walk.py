# Run inside Folio Page with FOLIO_ENGINE=native (FOLIO_TEST_SCRIPT): presses every ribbon
# control and menu item and writes /tmp/fw_walk.txt: tab, label, action(s), result —
# OK, NOT_YET (the new engine refused it), ERROR (an exception), SKIP.
# Picture Format / Shape Format / table tabs run with such an object selected.
import os
import sys
import time
import traceback

from gi.repository import Gtk

OUT = open(os.environ.get("WALK_OUT", "/tmp/fw_walk.txt"), "w")
flag = {"ny": False}
UI = {"n": 0}


def _cancel(self, *a):
    UI["n"] += 1
    return Gtk.ResponseType.CANCEL


Gtk.Dialog.run = _cancel
Gtk.NativeDialog.run = _cancel
_popup = Gtk.Popover.popup
Gtk.Popover.popup = lambda self: (UI.__setitem__("n", UI["n"] + 1), _popup(self))[1]
_menu = Gtk.Menu.popup_at_pointer
Gtk.Menu.popup_at_pointer = lambda self, *a: UI.__setitem__("n", UI["n"] + 1)
for n in ("info", "message", "confirm", "ask_text", "error", "warn"):
    if hasattr(win.dialogs, n):
        setattr(win.dialogs, n, lambda *a, **k: None)
_flash = win.status.flash


def flash(msg, *a, **k):
    if "new engine" in str(msg):
        flag["ny"] = True
    return _flash(msg, *a, **k)


win.status.flash = flash
win.actions._not_yet = lambda: flag.__setitem__("ny", True)
SEEN = []
_run = win.actions.run


def run(action):
    SEEN.append(action if isinstance(action, (str, tuple)) else getattr(action, "__name__", "fn"))
    return _run(action)


win.actions.run = run
# classic-engine paths: the document model asked for (None with the new engine), or a part
# of the old interface the new engine doesn't answer
MODEL = {"n": 0, "what": set()}
eng = win.engine
eng.__dict__.pop("model", None)
type(eng).model = property(lambda self: (MODEL.__setitem__("n", MODEL["n"] + 1), None)[1])
from folio.native import uno_model as _um  # noqa: E402
_ga = _um.NativeModel.__getattr__


def _logged(self, k):
    MODEL["what"].add(k)
    return _ga(self, k)


_um.NativeModel.__getattr__ = _logged
ERR = []
sys.excepthook = lambda t, v, tb: ERR.append("".join(traceback.format_exception(t, v, tb))[-400:])
SKIP = ("print", "close", "exit", "quit", "new-window", "open", "share", "backstage", "save", "macro",
        "read-aloud", "speak", "dictate", "help", "record")


def pump(t=0.15):
    end = time.time() + t
    while time.time() < end:
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)
        time.sleep(0.005)


def name_of(c):
    for a in ("label_text", "tooltip_text"):
        v = getattr(c, a, None)
        if v:
            return v
    try:
        return c.get_label() or ""
    except Exception:
        return ""


def items_of(tabs=None, exclude=()):
    out = []
    for c in list(win.ribbon.controls):
        tab = getattr(c, "tab_name", "?")
        if (tabs and tab not in tabs) or tab in exclude:
            continue
        if getattr(c, "action", None) is not None:
            out.append((tab, name_of(c), lambda c=c: c.run()))
        m = getattr(c, "menu", None)
        if callable(m) and not isinstance(m, Gtk.Widget):
            # galleries built when opened (Cover Page, WordArt...): their items as lists
            fn_m = getattr(c, "menu_fn", None) or m
            try:
                got = fn_m()
            except Exception:
                got = None
            m = got if isinstance(got, list) else None
            if isinstance(got, Gtk.Widget) and getattr(c, "tab_name", "") not in ("File",):
                def buttons(w, acc):
                    if isinstance(w, Gtk.Button) and not isinstance(w, (Gtk.MenuButton,)):
                        lab = w.get_label() or w.get_tooltip_text() or ""
                        if not lab:
                            for ch in (w.get_children() if isinstance(w, Gtk.Container) else []):
                                if isinstance(ch, Gtk.Label):
                                    lab = ch.get_text()
                                elif isinstance(ch, Gtk.Box):
                                    for x in ch.get_children():
                                        if isinstance(x, Gtk.Label):
                                            lab = lab or x.get_text()
                        if lab:
                            acc.append((lab.replace("_", ""), w))
                        return acc
                    if isinstance(w, Gtk.Container):
                        for ch in w.get_children():
                            buttons(ch, acc)
                    return acc
                for lab, b in buttons(got, []):
                    out.append((tab, name_of(c) + " > " + lab, lambda b=b: b.clicked()))
                try:
                    got.popdown() if hasattr(got, "popdown") else None
                except Exception:
                    pass
        if isinstance(m, list):
            for it in m:
                if isinstance(it, tuple) and len(it) >= 2 and it[0] != "#" and callable(it[1]):
                    out.append((tab, name_of(c) + " > " + str(it[0]), it[1]))
    return out


def walk(items, setup=None):
    for tab, label, fn in items:
        if any(s in label.lower() for s in SKIP):
            OUT.write("%s\t%s\t-\tSKIP\n" % (tab, label))
            continue
        if setup:
            setup()
        flag["ny"] = False
        UI["n"] = 0
        MODEL["n"] = 0
        MODEL["what"] = set()
        tops = {id(w) for w in Gtk.Window.list_toplevels() if w.get_visible()}
        panes = sum(len(sl.get_children()) for sl in (getattr(win, "left_pane_slot", None), getattr(win, "right_pane_slot", None)) if sl is not None)
        st0 = (win.engine.view.get_zoom(), getattr(win.engine.view, "marks", None), win.ribbon.current.name if getattr(win.ribbon, "current", None) else "")
        del SEEN[:]
        e = win.engine.ed
        try:
            e.mark_saved()
        except Exception:
            pass
        n0 = len(ERR)
        try:
            fn()
            pump(0.1)
            res = "ERROR" if len(ERR) > n0 else ("NOT_YET" if flag["ny"] else "OK")
            if res == "OK":
                if win.engine.ed.modified:
                    res = "CHANGED"
                else:
                    tops2 = {id(w) for w in Gtk.Window.list_toplevels() if w.get_visible()}
                    panes2 = sum(len(sl.get_children()) for sl in (getattr(win, "left_pane_slot", None), getattr(win, "right_pane_slot", None)) if sl is not None)
                    st1 = (win.engine.view.get_zoom(), getattr(win.engine.view, "marks", None), win.ribbon.current.name if getattr(win.ribbon, "current", None) else "")
                    res = "UI" if (UI["n"] or tops2 - tops or panes2 != panes or st1 != st0) else "SAME"
        except Exception as e:
            res = "ERROR " + repr(e)[:200]
        if res == "ERROR":
            res += " " + ERR[-1].replace("\n", " | ")[-300:]
        for w in Gtk.Window.list_toplevels():
            if w is not win and w.get_visible() and w.get_transient_for() is win:
                w.hide()
        if MODEL["n"] or MODEL["what"]:
            res += " MODEL%s" % ("(" + ",".join(sorted(MODEL["what"])) + ")" if MODEL["what"] else "")
        OUT.write("%s\t%s\t%s\t%s\n" % (tab, label, " ; ".join(str(s) for s in SEEN)[:200], res))
        OUT.flush()


ed = win.engine.ed
win.engine.command(".uno:InsertText", {"Text": "Hello world. Second sentence here.\nAnother paragraph of text."})
pump(0.3)
OBJ = ("Picture Format", "Shape Format", "Table Design", "Table Layout", "Chart Design", "SmartArt Design",
       "Equation", "Header & Footer", "Background Removal")
walk(items_of(exclude=OBJ))

# a picture, selected
pic = os.path.join(os.environ.get("FOLIO_SHARE", "/usr/share/folio-page"), "icons", "folio-page-128.png")


PICPOS = {}


def sel_picture():
    e = win.engine.ed
    if e.story() != "body":
        e.edit_notes(None)
    if not PICPOS:
        e.move_caret("doc_end", False)
        e.type_text("\n")
        e.insert_picture(pic)
        win.engine.view.after_edit()
        pump(0.3)
        o = e.selected_object()
        PICPOS.update(o or {})
    o = e.selected_object()
    if o is None or o["kind"] != "picture":
        pics = [n for n, _name, kind, _v in e.objects_list() if kind == "Picture"]
        if not pics:
            PICPOS.clear()
            return sel_picture()
        e.select_object_node(pics[0])
        win.engine.view.objs.refresh()
        win.engine.view.after_move()


sel_picture()
pump(0.3)
walk(items_of(tabs=("Picture Format",)), setup=sel_picture)


# a shape
def sel_shape():
    e = win.engine.ed
    if e.story() != "body":
        e.edit_notes(None)
    if e.selected_object() is None or e.selected_object()["kind"] == "picture":
        e.deselect_object()
        e.insert_shape("rect", 0, 300, 300, 100, 60, "Rectangle", False)
        win.engine.view.after_edit()


sel_shape()
win.update_object_tabs() if hasattr(win, "update_object_tabs") else None
pump(0.3)
walk(items_of(tabs=("Shape Format",)), setup=sel_shape)
print("DONE", flush=True)
OUT.close()
os._exit(0)
