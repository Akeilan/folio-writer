# Every action name the ribbon, menus and keyboard table mention: does the engine route it, or refuse it?
import os, sys, re, time, traceback
os.environ["WALK_OUT"] = "/tmp/p5out/p23_unused.txt"
_src = open(os.path.join(os.environ["FOLIO_WRITER_TESTS"], "native_command_walk.py")).read()
exec(_src.split("\ndef walk(")[0])
import folio
APP = os.path.dirname(folio.__file__)
names = {}
for f in os.listdir(APP):
    if not f.endswith(".py"): continue
    s = open(os.path.join(APP, f), encoding="utf8").read()
    for m in re.finditer(r'''\brun\(\s*["']([a-z][a-z0-9-]+)["']\s*\)''', s):
        names.setdefault(m.group(1), set()).add(f)
    if f == "keys.py":
        for m in re.finditer(r'''\(\s*"([^"]+)"\s*,\s*"([a-z.][A-Za-z0-9:.-]+)"\s*\)''', s):
            names.setdefault(m.group(2), set()).add("keys:" + m.group(1))
    if f == "ribbon_defs.py":
        for m in re.finditer(r'''"((?:cmd|ico)/[^"]*)"\s*,\s*"([a-z][a-z0-9-]+)"''', s):
            names.setdefault(m.group(2), set()).add(f)
out = open("/tmp/p5out/p23_actions.tsv", "w")
SKIPN = ("exit", "quit", "close", "close-window", "print", "new", "open", "save", "save-as", "new-window", "close-all")
e = win.engine.ed
for name in sorted(names):
    if name in SKIPN: continue
    try:
        while e.can_undo(): e.undo()
        e.select_all(); e.delete(True, False)
        e.type_text("Alpha beta gamma.\nSecond paragraph.")
        e.select_range(0, 6, 0, 10)
    except Exception:
        pass
    flag["ny"] = False; n0 = len(ERR)
    try:
        win.actions.run(name) if not name.startswith(".uno") else win.actions.cmd(name)
        pump(0.08)
        res = "ERROR " + ERR[-1].replace("\n", " | ")[-200:] if len(ERR) > n0 else ("NOT_YET" if flag["ny"] else "ok")
    except Exception as ex:
        res = "EXC " + repr(ex)[:200]
    out.write("%s\t%s\t%s\n" % (name, res, ",".join(sorted(names[name]))[:80])); out.flush()
    for w in Gtk.Window.list_toplevels():
        if w is not win and w.get_visible() and w.get_transient_for() is win:
            w.hide()
    try:
        if e.story() != "body": e.edit_notes(None)
    except Exception: pass
out.write("DONE\n"); out.close()
os._exit(0)
