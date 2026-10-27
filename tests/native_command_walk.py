import os, sys, traceback, json
from gi.repository import Gtk
OUT = open("/tmp/fw_walk.txt", "w")
flag = {"ny": False}
Gtk.Dialog.run = lambda self, *a: Gtk.ResponseType.CANCEL
Gtk.NativeDialog.run = lambda self, *a: Gtk.ResponseType.CANCEL
for n in ("info", "message", "confirm", "ask_text", "error", "warn"):
    if hasattr(win.dialogs, n):
        setattr(win.dialogs, n, lambda *a, **k: None)
orig_flash = win.status.flash
def flash(msg, *a, **k):
    if "new engine" in str(msg):
        flag["ny"] = True
    return orig_flash(msg, *a, **k)
win.status.flash = flash
_ny = win.actions._not_yet
def ny():
    flag["ny"] = True
win.actions._not_yet = ny
ERR = []
sys.excepthook = lambda t, v, tb: ERR.append("".join(traceback.format_exception(t, v, tb))[-300:])
SKIP = ("print", "close", "exit", "quit", "new-window", "open", "share", "backstage", "save", "macro", "read-aloud", "speak", "dictate", "help")

def pump(t=0.15):
    import time
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

items = []
for c in list(win.ribbon.controls):
    tab = getattr(c, "tab_name", "?")
    if getattr(c, "action", None) is not None:
        items.append((tab, name_of(c), c.action, lambda c=c: c.run()))
    m = getattr(c, "menu", None)
    if isinstance(m, list):
        for it in m:
            if isinstance(it, tuple) and len(it) >= 2 and it[0] != "#" and callable(it[1]):
                items.append((tab, name_of(c) + " > " + str(it[0]), "menu", it[1]))
print("ITEMS", len(items), flush=True)
win.engine.command(".uno:InsertText", {"Text": "Hello world. Second sentence here."}); pump(0.3)
for tab, label, action, fn in items:
    key = (str(label) + " " + str(action)).lower()
    if any(s in key for s in SKIP):
        OUT.write("%s\t%s\t%s\tSKIP\n" % (tab, label, action)); continue
    flag["ny"] = False
    n0 = len(ERR)
    try:
        fn()
        pump(0.1)
        res = "ERROR" if len(ERR) > n0 else ("NOT_YET" if flag["ny"] else "OK")
    except Exception as e:
        res = "ERROR " + repr(e)[:150]
    if res == "ERROR":
        res += " " + ERR[-1].replace("\n", " | ")[-200:]
    # close stray windows
    for w in Gtk.Window.list_toplevels():
        if w is not win and w.get_visible() and isinstance(w, (Gtk.Dialog, Gtk.Window)) and w.get_transient_for() is win:
            w.destroy()
    OUT.write("%s\t%s\t%s\t%s\n" % (tab, label, action, res)); OUT.flush()
OUT.close()
print("DONE", flush=True)
os._exit(0)
