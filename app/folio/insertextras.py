"""Insert extras: WordArt and Text Effects, Quick Parts (AutoText and
document properties), Signature Line, the Text Box gallery and Object."""
import json
import os

from gi.repository import GLib, Gtk

from .widgets import FDialog, combo, grid, heading

QUICKPARTS = os.path.join(os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config"),
                          "folio-writer", "quickparts.json")

# (name, fill colour, outline, shadow, bold)
EFFECTS = [
    ("Fill: Black, Text color 1; Shadow", 0x000000, False, True, False),
    ("Fill: Blue, Accent color 1; Shadow", 0x4472C4, False, True, False),
    ("Fill: Orange, Accent color 2; Outline: Orange", 0xED7D31, True, False, False),
    ("Fill: White; Outline: Blue, Accent color 1; Shadow", 0x4472C4, True, True, True),
    ("Fill: Gold, Accent color 4; Soft Bevel", 0xFFC000, False, True, True),
    ("Fill: Gray, Accent color 3; Sharp Bevel", 0x7F7F7F, False, True, True),
    ("Fill: Green, Accent color 6; Outline", 0x70AD47, True, False, True),
    ("Fill: Blue, Accent color 5; Outline: White", 0x5B9BD5, True, True, True),
    ("Fill: Black, Text color 1; Outline: White", 0x262626, True, True, True),
]


def apply_effect(target, idx):
    name, color, outline, shadow, bold = EFFECTS[idx]
    target.CharColor = color
    target.CharContoured = bool(outline)
    target.CharShadowed = bool(shadow)
    if bold:
        target.CharWeight = 150.0





# ------------------------------------------------------------ quick parts
def load_parts():
    try:
        with open(QUICKPARTS, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return []


def save_parts(parts):
    os.makedirs(os.path.dirname(QUICKPARTS), exist_ok=True)
    with open(QUICKPARTS, "w", encoding="utf-8") as f:
        json.dump(parts, f, ensure_ascii=False, indent=1)


GALLERIES = ["Quick Parts", "AutoText", "Cover Pages", "Headers", "Footers", "Text Boxes"]


def save_selection_as_part(win, default_gallery="Quick Parts"):
    view = win.engine.view
    try:
        html, _ = view.copy_selection("text/html")
        text, _ = view.copy_selection("text/plain;charset=utf-8")
    except Exception:
        html = text = None
    if not text:
        win.dialogs.message("Select the text you want to save first.")
        return
    d = FDialog(win, "Create New Building Block")
    name = Gtk.Entry(text=text.strip().split("\n")[0][:40])
    gallery = combo(GALLERIES, GALLERIES.index(default_gallery)
                    if default_gallery in GALLERIES else 0)
    d.add(grid([["_Name:", name], ["_Gallery:", gallery]]))
    if d.ask() == Gtk.ResponseType.OK and name.get_text().strip():
        parts = [p for p in load_parts() if p.get("name") != name.get_text().strip()]
        parts.append({"name": name.get_text().strip(), "gallery": gallery.get_active_text(),
                      "html": html or "", "text": text})
        save_parts(parts)
    d.done()


def insert_part(win, part):
    if part.get("html"):
        win.engine.paste_data("text/html", part["html"].encode("utf-8"))
    else:
        win.actions.insert_text(part.get("text", ""))


DOC_PROPS = [("Author", "author"), ("Title", "title"), ("Subject", "subject"),
             ("Company", None), ("Keywords", None), ("Comments", None), ("Status", None)]



def quick_parts_menu(win):
    from .ribbon import menu_popover
    parts = load_parts()
    items = []
    qp = [p for p in parts if p.get("gallery", "Quick Parts") == "Quick Parts"]
    for p in qp:
        items.append((p["name"], (lambda p=p: insert_part(win, p))))
    if qp:
        items.append(None)
    auto = [p for p in parts if p.get("gallery") == "AutoText"]
    sub = [("#", "AutoText")] + [(p["name"], (lambda p=p: insert_part(win, p)))
                                 for p in auto] + [None] if auto else []
    items += sub
    items += [("#", "Document Property")]
    items += [(n, (lambda n=n: win.model_call_sync("insertextras.insert_doc_property", n)))
              for n, _k in DOC_PROPS]
    items += [None, ("Field...", lambda: win.run("field-dialog")),
              ("Building Blocks Organizer...", lambda: organizer(win)),
              None, ("Save Selection to Quick Part Gallery...",
                     lambda: save_selection_as_part(win))]
    return menu_popover(None, items)


def organizer(win):
    parts = load_parts()
    d = FDialog(win, "Building Blocks Organizer", buttons=(("Close", Gtk.ResponseType.CLOSE),))
    d.set_default_size(520, 360)
    store = Gtk.ListStore(str, str)
    for p in parts:
        store.append([p["name"], p.get("gallery", "Quick Parts")])
    tv = Gtk.TreeView(model=store)
    for i, h in enumerate(("Name", "Gallery")):
        tv.append_column(Gtk.TreeViewColumn(h, Gtk.CellRendererText(), text=i))
    sw = Gtk.ScrolledWindow()
    sw.set_size_request(480, 260)
    sw.add(tv)
    d.add(sw, expand=True)
    bar = Gtk.Box(spacing=6)
    ins = Gtk.Button(label="_Insert", use_underline=True)
    dele = Gtk.Button(label="_Delete", use_underline=True)

    def sel():
        model, it = tv.get_selection().get_selected()
        return model[it][0] if it else None

    def do_insert(*_):
        n = sel()
        for p in load_parts():
            if p["name"] == n:
                d.response(Gtk.ResponseType.CLOSE)
                GLib.idle_add(lambda p=p: (insert_part(win, p), False)[1])

    def do_delete(*_):
        n = sel()
        if n:
            save_parts([p for p in load_parts() if p["name"] != n])
            model, it = tv.get_selection().get_selected()
            model.remove(it)
    ins.connect("clicked", do_insert)
    dele.connect("clicked", do_delete)
    bar.pack_start(ins, False, False, 0)
    bar.pack_start(dele, False, False, 0)
    d.add(bar)
    d.ask()
    d.done()


# ------------------------------------------------------------ signature line
def signature_dialog(win):
    d = FDialog(win, "Signature Setup")
    signer = Gtk.Entry()
    title = Gtk.Entry()
    email = Gtk.Entry()
    date = Gtk.CheckButton.new_with_mnemonic("Show sign _date in signature line")
    for e in (signer, title, email):
        e.set_width_chars(36)
    d.add(grid([["Suggested _signer:", signer], ["Suggested signer's _title:", title],
                ["Suggested signer's _e-mail address:", email]]))
    d.add(date)
    if d.ask() == Gtk.ResponseType.OK:
        vals = (signer.get_text(), title.get_text(), email.get_text(), date.get_active())
        native_signature_line(win, *vals)
    d.done()


def native_signature_line(win, signer, title, email, with_date):
    """The signature block (an X on a line, the signer's details under it)."""
    ed = win.engine.ed
    p, off = ed.caret_pos()
    lines = [s for s in (signer, title, email) if s]
    if with_date:
        lines.append("Date: " + __import__("datetime").date.today().strftime("%-m/%-d/%Y"))
    entries = [("X", True)] + [(s, False) for s in lines]
    ed.begin_group("Signature Line")
    try:
        if off > 0:
            ed.type_text("\n")
        ed.type_text("\n")
        ed.move_caret("left", False)
        line = [("w:val", "single"), ("w:sz", "12"), ("w:space", "1"), ("w:color", "000000")]
        for i, (txt, is_line) in enumerate(entries):
            if i:
                ed.type_text("\n")
            ed.set_borders("paras", [(s, None) for s in ("top", "left", "right", "between")] +
                           [("bottom", line if is_line else None)])
            ed.apply_para([("w:spacing", [("w:before", "360" if is_line else "0"), ("w:after", "0")]),
                           ("w:ind", [("w:right", "4320" if is_line else "0")])], "Signature Line")
            q, start = ed.caret_pos()
            ed.type_text(txt)
            q2, end = ed.caret_pos()
            ed.select_nodes(q, start, q2, end)
            ed.apply_run([("w:sz", [("w:val", "40" if is_line else "22")])], "Signature Line")
            ed.select_nodes(q2, end, q2, end)
    finally:
        ed.end_group()
    win.engine.view.after_edit()



# ------------------------------------------------------------ text box gallery
TEXTBOXES = [("Simple Text Box", "simple"), ("Sidebar", "sidebar"), ("Quote", "quote"),
             ("Banded", "banded")]



# ------------------------------------------------------------ object
def object_dialog(win):
    d = FDialog(win, "Object")
    nb = Gtk.Notebook()
    new_list = Gtk.ListBox()
    kinds = [("Chart", "chart"), ("Equation", "equation"), ("Drawing (Text Box)", "textbox")]
    for label, _k in kinds:
        row = Gtk.ListBoxRow()
        row.add(Gtk.Label(label=label, xalign=0))
        new_list.add(row)
    new_list.select_row(new_list.get_row_at_index(0))
    p1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    p1.set_border_width(10)
    p1.pack_start(Gtk.Label(label="Object type:", xalign=0), False, False, 0)
    p1.pack_start(new_list, True, True, 0)
    nb.append_page(p1, Gtk.Label(label="Create New"))
    p2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    p2.set_border_width(10)
    fc = Gtk.FileChooserButton(title="File")
    fc.set_width_chars(40)
    p2.pack_start(Gtk.Label(label="File name:", xalign=0), False, False, 0)
    p2.pack_start(fc, False, False, 0)
    note = Gtk.Label(label="Pictures are inserted as pictures; documents are inserted with "
                           "their contents.", xalign=0)
    note.set_line_wrap(True)
    note.get_style_context().add_class("dim-label")
    p2.pack_start(note, False, False, 0)
    nb.append_page(p2, Gtk.Label(label="Create from File"))
    d.add(nb, expand=True)
    if d.ask() == Gtk.ResponseType.OK:
        if nb.get_current_page() == 0:
            row = new_list.get_selected_row()
            kind = kinds[row.get_index() if row else 0][1]
            if kind == "chart":
                GLib.idle_add(lambda: (__import__(
                    "folio.native.charts",
                    fromlist=["x"]).insert_chart_dialog(win), False)[1])
            elif kind == "equation":
                win.run("equation")
            else:
                win.run(("draw-shape", "textbox"))
        else:
            path = fc.get_filename()
            if path:
                ext = os.path.splitext(path)[1].lower()
                if ext in (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg", ".tif", ".tiff",
                           ".webp"):
                    from .native import objects
                    objects.insert_picture_path(win, path)
                else:
                    from .native import insertfile
                    insertfile.insert(win, path)
    d.done()
