import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); # Word-parity scenario harness: exec'd by a test script after common.py.
# Scenarios are generators; `yield secs` waits while the app runs.
import subprocess, time, traceback, os
E = win.engine
exec(open(TESTS + "/word/wn.py").read())
RESULTS = []
CUR = {"name": "?"}

def K(*specs):
    for s in specs:
        subprocess.run(["xdotool", "key", "--clearmodifiers", s], env=dict(os.environ, DISPLAY=os.environ.get("DISPLAY", ":99")))
        time.sleep(0.06)

def T(text, delay=15):
    parts = text.split("\n")
    for i, part in enumerate(parts):
        if i:
            K("Return")
        if part:
            subprocess.run(["xdotool", "type", "--delay", str(delay), "--", part],
                           env=dict(os.environ, DISPLAY=os.environ.get("DISPLAY", ":99")))

def X(*args):
    subprocess.run(["xdotool"] + [str(a) for a in args], env=dict(os.environ, DISPLAY=os.environ.get("DISPLAY", ":99")))

def check(name, cond, detail=""):
    tag = "PASS" if cond else "FAIL"
    RESULTS.append((CUR["name"], name, tag, detail))
    log("%s [%s] %s %s" % (tag, CUR["name"], name, ("| " + str(detail)) if detail else ""))

def note(name, detail):
    log("NOTE [%s] %s | %s" % (CUR["name"], name, detail))

def focus():
    win.present()
    E.view.grab_focus()

def fresh():
    """Empty document with default formatting."""
    ed = E.ed
    if ed.story() == "notes":
        ed.edit_notes(None)
    elif ed.story() != "body":
        ed.edit_header_footer(None, False)
    try:
        ed.leave_textbox()
    except Exception:
        pass
    ed.deselect_object()
    ed.set_track_changes(False)
    ed.select_all()
    ed.delete(True, False)
    try:
        ed.remove_toc()
    except Exception:
        pass
    for _i in range(20):
        try:
            cc = ed.content_controls()
        except Exception:
            break
        if not cc:
            break
        ed.move_caret("doc_end", False)
        if not ed.remove_control(cc[0][0], False):
            break
    for _i in range(50):
        tbl = [b for b in ed.body_blocks() if b[0] == "t"]
        if not tbl:
            break
        try:
            p0 = ed.table_cells(tbl[0][2])[0][0][0]
            ed.select_nodes(p0, 0, p0, 0)
            ed.table_command("delete_table")
        except Exception:
            break
    for _i in range(200):
        if len(ed.body_blocks()) <= 1:
            break
        ed.move_caret("doc_end", False)
        ed.delete(False, False)
        if len(ed.body_blocks()) > 1 and not ed.para_text_of(ed.caret_pos()[0]):
            ed.move_caret("doc_start", False)
            ed.delete(True, False)
    ed.select_all()
    ed.delete(True, False)
    for _i in range(20):
        try:
            objs = ed.objects_list()
            if not objs:
                break
            ed.select_object_node(objs[0][0])
            ed.object_delete()
        except Exception:
            break
    for fn in ("remove_list", "reset_para_formatting", "clear_formatting"):
        try:
            getattr(ed, fn)()
        except Exception:
            pass
    try:
        win.actions.apply_style("Normal")
    except Exception:
        pass
    ed.set_borders("paras", [(s, None) for s in ("top", "left", "bottom", "right", "between")])
    E.view.after_edit()
    focus()

def run_scenarios(*gens, outfile="/tmp/wc_results.txt"):
    gens = list(gens)
    state = {"g": None}
    def nxt():
        try:
            if state["g"] is None:
                if not gens:
                    with open(outfile, "a") as f:
                        for r in RESULTS:
                            f.write("\t".join(str(x) for x in r) + "\n")
                    log("ALLDONE")
                    GLib.timeout_add(300, lambda: app.quit() or False)
                    return False
                fn = gens.pop(0)
                CUR["name"] = fn.__name__
                state["g"] = fn()
            d = next(state["g"])
        except StopIteration:
            state["g"] = None
            d = 0.3
        except Exception:
            log("ERROR in", CUR["name"]); log(traceback.format_exc())
            check("scenario crashed", False, traceback.format_exc().splitlines()[-1])
            state["g"] = None
            d = 0.5
        GLib.timeout_add(int(max(0.05, d or 0.05) * 1000), nxt)
        return False
    GLib.timeout_add(500, nxt)

def screen_of_widget(widget, x, y):
    top = widget.get_toplevel()
    tx, ty = widget.translate_coordinates(top, int(x), int(y))
    ox, oy = top.get_window().get_origin()[1:]
    return ox + tx, oy + ty

def doc_screen(xt, yt):
    px, py = E.twips_to_px(xt, yt)
    return screen_of_widget(E.view, px, py)

def click(x, y, button=1, n=1, mods=None):
    X("mousemove", int(x), int(y)); time.sleep(0.08)
    if mods:
        X("keydown", mods)
    X("click", "--repeat", n, "--delay", 80, button)
    if mods:
        X("keyup", mods)

def widget_center(w):
    a = w.get_allocation()
    return screen_of_widget(w, a.width / 2, a.height / 2)

def find_widget(root, pred):
    out = []
    def walk(w):
        try:
            if pred(w): out.append(w)
        except Exception: pass
        if isinstance(w, Gtk.Container):
            for c in w.get_children(): walk(c)
    walk(root)
    return out

def dialogs_open():
    return [w for w in Gtk.Window.list_toplevels() if w.get_visible() and w is not win and isinstance(w, Gtk.Window) and w.get_title()]

def close_dialogs():
    for w in dialogs_open():
        if isinstance(w, Gtk.Dialog): w.response(Gtk.ResponseType.CANCEL)
        else:
            try: w.hide()
            except Exception: pass

def popups():
    return [w for w in Gtk.Window.list_toplevels() if w.get_visible() and w.get_window_type() == Gtk.WindowType.POPUP]

def menu_labels():
    out = []
    for w in popups():
        for mi in find_widget(w, lambda x: isinstance(x, Gtk.MenuItem)):
            lab = mi.get_label() or " ".join(l.get_text() for l in find_widget(mi, lambda x: isinstance(x, Gtk.Label)))
            out.append(lab or "")
        for mb in find_widget(w, lambda x: isinstance(x, Gtk.ModelButton)):
            out.append(mb.get_property("text") or "")
        for b in find_widget(w, lambda x: isinstance(x, Gtk.Button) and not isinstance(x, Gtk.ModelButton)):
            if b.get_label(): out.append(b.get_label())
            elif b.get_tooltip_text(): out.append("tip:" + b.get_tooltip_text())
    return out

def _clean(s):
    return (s or "").replace("\n", " ").replace("_", "").strip()

def find_control(tab, label):
    for c in win.ribbon.controls:
        if getattr(c, "tab_name", "") != tab:
            continue
        lab = _clean(getattr(c, "label", "")) or _clean((getattr(c, "tooltip_text", "") or "").split(" (")[0])
        if lab.lower() == label.lower():
            return c
    return None

def rib(tab, label, item=None):
    """Run a ribbon button (or one of its menu items) as a click would, later."""
    c = find_control(tab, label)
    if c is None:
        check("ribbon control exists: %s > %s" % (tab, label), False)
        return False
    if item is None:
        GLib.idle_add(lambda: (c.run(), False)[1])
        return True
    items = getattr(c, "menu", None)
    if callable(items):
        try:
            items = items()
        except TypeError:
            items = None
    if isinstance(items, Gtk.Popover):
        for b in find_widget(items, lambda w: isinstance(w, Gtk.Button)):
            labs = [l.get_text() for l in find_widget(b, lambda w: isinstance(w, Gtk.Label))]
            if any(_clean(l).lower() == item.lower() for l in labs):
                GLib.idle_add(lambda b=b: (b.clicked(), False)[1])
                return True
        items = None
    if isinstance(items, (list, tuple)):
        for it in items:
            if it is not None and not isinstance(it, Gtk.Widget) and it[0] != "#" and \
                    (_clean(it[0]).lower() == item.lower() or _clean(it[0]).lower().startswith(item.lower() + " ")) and callable(it[1]):
                GLib.idle_add(lambda f=it[1]: (f(), False)[1])
                return True
    check("ribbon menu item exists: %s > %s > %s" % (tab, label, item), False,
          [it[0] for it in items or [] if it and not isinstance(it, Gtk.Widget)][:30])
    return False

def dlg(title_part):
    return [d for d in dialogs_open() if title_part.lower() in (d.get_title() or "").lower()]

def respond(title_part, resp=Gtk.ResponseType.OK):
    for d in dlg(title_part):
        if isinstance(d, Gtk.Dialog):
            d.response(resp)
