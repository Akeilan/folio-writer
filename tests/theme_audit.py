# X2-01: run inside Folio Page (FOLIO_TEST_SCRIPT, native engine) started under
# GTK_THEME=Adwaita:dark or FolioTestColour (tools/run_theme_audit.sh). Every ribbon tab,
# the File view, the panes, a comment balloon, every dialog and menu a ribbon command opens
# keep the app's own colours; text stays readable.
import os
import sys
import time
import traceback

sys.path.insert(0, os.path.dirname(os.environ["FOLIO_TEST_SCRIPT"]))
import themecheck  # noqa: E402
from gi.repository import Gtk  # noqa: E402

OUT = os.environ.get("UI_OUT", "/tmp/theme_out")
os.makedirs(OUT, exist_ok=True)
FAILS = []
CHECKED = []


def pump(t=0.2):
    end = time.time() + t
    while time.time() < end:
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)
        time.sleep(0.003)


def look(w, where):
    pump(0.2)
    try:
        probs = themecheck.audit(w, where)
    except Exception as e:
        probs = ["%s: audit failed %r" % (where, e)]
    CHECKED.append(where)
    for p in probs:
        print("FAIL " + p, flush=True)
    if probs:
        themecheck.save(w, os.path.join(OUT, "theme_%s_%s.png" % (
            themecheck.mode(), "".join(c if c.isalnum() else "_" for c in where)[:60])))
    FAILS.extend(probs)


def main():
    print("theme", os.environ.get("GTK_THEME"), "mode", themecheck.mode(), flush=True)
    ed = win.engine.ed
    ed.type_text("Theme audit text. Second sentence here.")
    win.engine.view.after_edit()
    pump(0.3)
    # ---- ribbon tabs
    for tab in list(win.ribbon.tabs):
        b = getattr(tab, "button", None)
        if b is not None and not b.get_visible():
            continue
        win.ribbon.select(tab)
        look(win, "tab " + tab.name)
    win.ribbon.select(win.ribbon.tabs[0])
    # ---- File view
    for page in ("home", "new", "open", "info", "saveas", "print", "share", "export"):
        try:
            win.show_backstage(page)
            look(win, "file " + page)
        except Exception as e:
            FAILS.append("file %s: %r" % (page, e))
    win.backstage.close()
    pump()
    # ---- panes and a comment balloon
    from folio import panes as P
    for cls in (P.NavigationPane, P.StylesPane, P.ClipboardPane, P.ThesaurusPane):
        try:
            win.show_pane(cls, "left" if cls is P.NavigationPane else "right")
            pump(0.4)
            look(win, "pane " + cls.__name__)
            win.hide_pane(win.panes.get(cls))
        except Exception as e:
            FAILS.append("pane %s: %r" % (cls.__name__, e))
    ed.select_all()
    cid = win.comments.new_comment()
    pump(0.5)
    look(win, "comment balloon typing")
    win.comments.finish()
    pump(0.3)
    # ---- every dialog and menu a ribbon command opens, once per title
    seen = set()

    def look_run(d):
        t = d.get_title() or type(d).__name__
        if isinstance(d, Gtk.FileChooserDialog):
            # the desktop's own file dialog: it follows the desktop theme, as it should
            return Gtk.ResponseType.CANCEL
        if t not in seen:
            seen.add(t)
            d.show_all()
            pump(0.25)
            look(d, "dialog " + t)
        return Gtk.ResponseType.CANCEL

    Gtk.Dialog.run = look_run
    Gtk.NativeDialog.run = lambda d: Gtk.ResponseType.CANCEL
    Gtk.PrintOperation.run = lambda *a: Gtk.PrintOperationResult.CANCEL
    _popup = Gtk.Popover.popup

    def pop(p):
        _popup(p)
        rel = p.get_relative_to()
        key = "menu " + (getattr(rel, "tooltip_text", None) or (rel.get_tooltip_text() if rel else "") or "?")
        if key not in seen and len(seen) < 400:
            seen.add(key)
            pump(0.2)
            look(p, key)
        p.popdown()
    Gtk.Popover.popup = pop
    Gtk.Menu.popup_at_pointer = lambda *a: None
    for n in ("info", "message", "confirm", "ask_text", "error", "warn"):
        if hasattr(win.dialogs, n):
            setattr(win.dialogs, n, lambda *a, **k: None)
    skip = ("print", "close", "exit", "quit", "new-window", "open", "share", "backstage", "save",
            "macro", "read-aloud", "speak", "dictate", "help", "record")
    # every drop-down menu of the ribbon (popover under its button's tab)
    for tab in list(win.ribbon.tabs):
        b = getattr(tab, "button", None)
        if b is not None and not b.get_visible():
            continue
        win.ribbon.select(tab)
        pump(0.1)
        for c in list(win.ribbon.controls):
            if getattr(c, "tab_name", "") != tab.name or not hasattr(c, "open_menu") or getattr(c, "menu", None) is None:
                continue
            if not c.get_mapped():
                continue
            try:
                pop = c.open_menu()
            except Exception:
                continue
            pump(0.15)
            nm = getattr(c, "label_text", None) or c.get_tooltip_text() or "?"
            if pop is not None and pop.get_mapped():
                key = "menu %s > %s" % (tab.name, nm)
                if key not in seen:
                    seen.add(key)
                    look(pop, key)
                pop.popdown()
            pump(0.05)
    win.ribbon.select(win.ribbon.tabs[0])
    for c in list(win.ribbon.controls):
        name = (getattr(c, "label_text", None) or getattr(c, "tooltip_text", None) or "").lower()
        if any(s in name for s in skip) or getattr(c, "action", None) is None:
            continue
        tab = getattr(c, "tab_name", "")
        if tab in ("Picture Format", "Shape Format", "Table Design", "Table Layout", "Chart Design",
                   "SmartArt Design", "Equation", "Header & Footer", "Background Removal"):
            continue
        try:
            ed.mark_saved()
            c.run()
        except Exception:
            pass
        pump(0.05)
        for w in Gtk.Window.list_toplevels():
            if w is not win and w.get_mapped() and w.get_transient_for() is win:
                t = w.get_title() or type(w).__name__
                if t not in seen and w.get_window() is not None:
                    seen.add(t)
                    look(w, "window " + t)
                w.hide()
        if win.backstage.get_visible():
            win.backstage.close()
    kinds = {}
    for c in CHECKED:
        kinds[c.split(" ")[0]] = kinds.get(c.split(" ")[0], 0) + 1
    print("checked:", len(CHECKED), kinds, flush=True)


try:
    main()
except Exception:
    traceback.print_exc()
    FAILS.append("exception")
print("THEME FAILED: %d" % len(FAILS) if FAILS else "THEME all passed", flush=True)
try:
    win.engine.ed.mark_saved()
except Exception:
    pass
os._exit(1 if FAILS else 0)
