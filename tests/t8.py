exec(open("/home/claude/folio2/tests/common.py").read())
import sys, traceback
e = win.engine
A = win.actions
events = []
e.connect("engine-dialog", lambda en, t: log("ENGINE DIALOG", t, "during", cur[0]))
cur = [None]
def closer():
    for w in Gtk.Window.list_toplevels():
        if w is win:
            continue
        if isinstance(w, Gtk.Dialog) and w.get_visible():
            log("  our dialog:", w.get_title(), "during", cur[0])
            w.response(Gtk.ResponseType.CANCEL)
        elif isinstance(w, Gtk.Window) and w.get_visible() and w.get_type_hint() == 1 and w.get_title():
            log("  our window:", w.get_title(), "during", cur[0])
            w.destroy()
    return True
GLib.timeout_add(700, closer)
def popdown_all():
    def walk(w):
        if isinstance(w, Gtk.Popover):
            w.popdown()
    for c in win.ribbon.controls:
        pass
def prep():
    A.insert_text("Hello world, this is some text. ")
def prep2():
    e.command(".uno:SelectWord")
items = []
from folio.ribbon import SplitButton, MenuButton, RibbonButton, ComboControl
for c in win.ribbon.controls:
    name = (getattr(c, "label_text", None) or getattr(c, "tooltip_text", "") or type(c).__name__)
    if isinstance(c, SplitButton) and isinstance(c.menu, list):
        for it in c.menu:
            if it and it[0] != "#" and len(it) > 1 and callable(it[1]):
                items.append(("%s > %s" % (name, it[0]), it[1]))
    act = getattr(c, "action", None)
    if act is not None and not isinstance(c, ComboControl):
        items.append((name, lambda c=c: c.ribbon.run(c.action)))
SKIP = ("Close", "New\nWindow", "New Window", "Save", "Read\nMode", "Read Mode", "Focus")
log("items", len(items))
fns = [prep, prep2]
for label, fn in items:
    if any(label.startswith(s) for s in SKIP):
        continue
    def f(label=label, fn=fn):
        cur[0] = label; log("RUN", label.replace("\n"," "))
        try:
            fn()
        except Exception:
            log("EXC", label, traceback.format_exc().splitlines()[-1])
    fns.append(f)
fns.append(lambda: (log("done"), app.quit()))
win.ribbon.all_controls()
steps(*fns, delay=900)
