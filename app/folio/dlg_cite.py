"""Dialogs for citations: Create Source, Source Manager, Insert Citation menu."""
from gi.repository import GLib, Gtk, Pango

from . import citations as C
from .widgets import FDialog, combo, grid, heading


def source_dialog(win, src=None, title="Create Source"):
    """Returns the edited source dict, or None."""
    src = dict(src or {"type": "Book"})
    d = FDialog(win, title if not src.get("tag") or title != "Create Source" else "Edit Source")
    d.set_default_size(520, -1)
    types = [t for t, _c in C.TYPES]
    tcombo = combo(types, src.get("type", "Book"))
    d.add(grid([["Type of _Source:", tcombo]]))
    m = win.engine.model
    d.add(heading("Bibliography Fields for %s" % (C.current_style(m) if m is not None
                                                  else "APA")))
    holder = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    d.add(holder)
    entries = {}
    values = dict(src)

    def build(*_):
        for k, e in entries.items():
            values[k] = e.get_text()
        for ch in holder.get_children():
            holder.remove(ch)
        entries.clear()
        rows = []
        for key, label in C.FIELDS[tcombo.get_active_text() or "Book"]:
            e = Gtk.Entry(text=values.get(key, ""))
            e.set_width_chars(40)
            if key == "author":
                e.set_placeholder_text("Last, First; Last, First")
            entries[key] = e
            rows.append([label + ":", e])
        holder.pack_start(grid(rows), False, False, 0)
        holder.show_all()
    tcombo.connect("changed", build)
    build()
    tag = Gtk.Entry(text=src.get("tag", ""))
    tag.set_width_chars(16)
    tag.set_placeholder_text("(automatic)")
    d.add(grid([["_Tag name:", tag]]))
    r = d.ask()
    out = None
    if r == Gtk.ResponseType.OK:
        out = {k: v for k, v in values.items() if not k.startswith("_")}
        for k, e in entries.items():
            out[k] = e.get_text().strip()
        out["type"] = tcombo.get_active_text() or "Book"
        out["tag"] = tag.get_text().strip() or src.get("tag", "")
        out = {k: v for k, v in out.items() if v}
        if src.get("tag"):
            out["_editing"] = True
    d.done()
    return out


def citation_menu(win):
    """Insert Citation drop-down: the document's sources, then Add New Source."""
    from .ribbon import menu_popover
    m = win.engine.model
    items = []
    if m is not None:
        style = C.current_style(m)
        for s in sorted(C.doc_sources(m), key=lambda s: (s.get("author") or s.get("title") or "")):
            label = "%s\n%s" % (C.author_list(s, style) or s.get("tag"),
                                (s.get("title") or "")[:60])
            items.append((label, (lambda t=s["tag"]: insert(win, t))))
        if items:
            items.append(None)
    if m is not None and C.citation_at_cursor(m) is not None:
        items = [("Edit Citation...", lambda: edit_citation(win)), None] + items
    items += [("Add New Source...", lambda: new_source(win, cite=True)),
              ("Add New Placeholder...", lambda: placeholder(win))]
    return menu_popover(None, items)


def insert(win, tag):
    m = win.engine.model
    if m is not None:
        C.insert_citation(m, tag)


def new_source(win, cite=False):
    m = win.engine.model
    if m is None:
        return
    src = source_dialog(win)
    if src:
        src = C.add_source(m, src)
        if cite:
            C.insert_citation(m, src["tag"])


def placeholder(win):
    m = win.engine.model
    if m is None:
        return
    name = win.dialogs.ask_text("Placeholder Name", "Type the tag name of the source. You "
                                "can add more information to this source later by "
                                "clicking Edit in the Source Manager.",
                                "Placeholder%d" % (len(C.doc_sources(m)) + 1))
    if name:
        src = C.add_source(m, {"tag": name.strip(), "title": name.strip(), "type": "Book",
                               "author": name.strip()}, master=False)
        C.insert_citation(m, src["tag"])


def manage_sources(win):
    m = win.engine.model
    if m is None:
        return
    d = FDialog(win, "Source Manager", buttons=(("Close", Gtk.ResponseType.CLOSE),))
    d.set_default_size(820, 520)
    d.set_resizable(True)
    style = C.current_style(m)

    def make_list():
        store = Gtk.ListStore(str, str)      # label, tag
        tv = Gtk.TreeView(model=store)
        tv.set_headers_visible(False)
        cell = Gtk.CellRendererText()
        cell.set_property("ellipsize", Pango.EllipsizeMode.END)
        tv.append_column(Gtk.TreeViewColumn("", cell, text=0))
        sw = Gtk.ScrolledWindow()
        sw.set_size_request(340, 280)
        sw.add(tv)
        return store, tv, sw

    mstore, mtv, msw = make_list()
    cstore, ctv, csw = make_list()
    cited_note = Gtk.Label(xalign=0)

    def label(s):
        mark = "✓ " if C.is_cited(m, s.get("tag")) else "    "
        return "%s%s; %s (%s)" % (mark, s.get("author") or "", s.get("title") or "",
                                  s.get("year") or "")

    search = Gtk.SearchEntry()
    search.set_placeholder_text("Type to search citations")
    sort = combo(["Sort by Author", "Sort by Tag", "Sort by Title", "Sort by Year"], 0)

    def order(lst):
        key = ["author", "tag", "title", "year"][max(0, sort.get_active())]
        q = search.get_text().strip().lower()
        if q:
            lst = [x for x in lst if any(q in str(x.get(k) or "").lower()
                                         for k in ("author", "title", "tag", "year"))]
        return sorted(lst, key=lambda x: str(x.get(key) or "").lower())

    def fill(*_):
        mstore.clear()
        cstore.clear()
        for s in order(C.master_sources()):
            mstore.append(["%s; %s (%s)" % (s.get("author") or "", s.get("title") or "",
                                            s.get("year") or ""), s.get("tag")])
        for s in order(C.doc_sources(m)):
            cstore.append([label(s), s.get("tag")])
    search.connect("search-changed", fill)
    sort.connect("changed", fill)
    fill()

    def selected(tv):
        model, it = tv.get_selection().get_selected()
        return model[it][1] if it else None

    def find(tag, lst):
        for s in lst:
            if s.get("tag") == tag:
                return s
        return None

    preview = Gtk.Label(xalign=0)
    preview.set_line_wrap(True)
    preview.set_max_width_chars(90)
    preview.set_selectable(True)

    def show_preview(tv, lst_fn):
        tag = selected(tv)
        s = find(tag, lst_fn()) if tag else None
        if s is None:
            preview.set_text("")
            return
        cite = C.citation_text(s, style)
        parts = "".join(("<i>%s</i>" if it else "%s") % GLib.markup_escape_text(t)
                        for t, it in C.entry_parts(s, style))
        preview.set_markup("<b>Citation:</b>  (%s)\n\n<b>Bibliography Entry:</b>\n%s" % (
            GLib.markup_escape_text(cite), parts))
    mtv.get_selection().connect("changed", lambda *_: show_preview(mtv, C.master_sources))
    ctv.get_selection().connect("changed", lambda *_: show_preview(ctv,
                                                                    lambda: C.doc_sources(m)))

    def copy_to_doc(*_):
        s = find(selected(mtv), C.master_sources())
        if s:
            C.add_source(m, dict(s), master=False)
            fill()

    def copy_to_master(*_):
        s = find(selected(ctv), C.doc_sources(m))
        if s:
            C.add_to_master(dict(s))
            fill()

    def delete(*_):
        tag = selected(ctv)
        if tag:
            if C.is_cited(m, tag):
                win.dialogs.message("This source is cited in the document. Remove its "
                                    "citations first.")
                return
            C.delete_source(m, tag)
        else:
            tag = selected(mtv)
            if tag:
                C.save_master([s for s in C.master_sources() if s.get("tag") != tag])
        fill()

    def edit(*_):
        tag = selected(ctv)
        s = find(tag, C.doc_sources(m)) if tag else None
        if s is None:
            return
        out = source_dialog(win, s, "Edit Source")
        if out:
            C.add_source(m, out)
            fill()

    def new(*_):
        out = source_dialog(win)
        if out:
            C.add_source(m, out)
            fill()

    top = Gtk.Box(spacing=8)
    top.pack_start(Gtk.Label(label="Search:"), False, False, 0)
    top.pack_start(search, True, True, 0)
    top.pack_start(sort, False, False, 0)
    d.add(top)
    lists = Gtk.Box(spacing=8)
    left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
    left.pack_start(Gtk.Label(label="Master List", xalign=0), False, False, 0)
    left.pack_start(msw, True, True, 0)
    mid = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    mid.set_valign(Gtk.Align.CENTER)
    for text, cb in (("Copy ->", copy_to_doc), ("<- Copy", copy_to_master), ("Delete", delete),
                     ("Edit...", edit), ("New...", new)):
        b = Gtk.Button(label=text)
        b.connect("clicked", cb)
        mid.pack_start(b, False, False, 0)
    right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
    right.pack_start(Gtk.Label(label="Current List", xalign=0), False, False, 0)
    right.pack_start(csw, True, True, 0)
    note = Gtk.Label(label="✓ cited source", xalign=0)
    note.get_style_context().add_class("dim-label")
    right.pack_start(note, False, False, 0)
    lists.pack_start(left, True, True, 0)
    lists.pack_start(mid, False, False, 0)
    lists.pack_start(right, True, True, 0)
    d.add(lists, expand=True)
    d.add(heading("Preview (%s):" % style))
    d.add(preview)
    d.ask()
    d.done()


def edit_citation(win):
    m = win.engine.model
    f = C.citation_at_cursor(m) if m is not None else None
    if f is None:
        win.dialogs.message("Put the cursor in a citation first.")
        return
    tag, opts = C.citation_info(m, f)
    d = FDialog(win, "Edit Citation")
    d.add(heading("Add"))
    pages = Gtk.Entry(text=opts.get("pages", ""))
    pages.set_width_chars(12)
    d.add(grid([["_Pages:", pages]]))
    d.add(heading("Suppress"))
    sup = set(opts.get("suppress") or ())
    checks = {}
    row = Gtk.Box(spacing=14)
    for key, label in (("author", "_Author"), ("year", "_Year"), ("title", "_Title")):
        cb = Gtk.CheckButton.new_with_mnemonic(label)
        cb.set_active(key in sup)
        checks[key] = cb
        row.pack_start(cb, False, False, 0)
    d.add(row)
    if d.ask() == Gtk.ResponseType.OK:
        new = {}
        if pages.get_text().strip():
            new["pages"] = pages.get_text().strip()
        s2 = [k for k, cb in checks.items() if cb.get_active()]
        if s2:
            new["suppress"] = s2
        win.engine.sync(lambda: C.set_citation_options(m, f, new))
    d.done()
