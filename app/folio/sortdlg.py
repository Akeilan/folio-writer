"""Sort, as in the original: Sort by / Then by / Then by, each with a type,
a 'Using' part and a direction; a header row; options for the field
separator, column-only sorting, case and language."""
import uno
from gi.repository import Gtk

from . import bridge, docapi
from .widgets import FDialog, combo, heading

TYPES = [("Text", 2), ("Number", 1), ("Date", 0)]


def _rows(m):
    """('table', table, first row text) or ('text', paragraphs) for the
    selection."""
    vc = docapi.view_cursor(m)
    try:
        t = vc.TextTable
    except Exception:
        t = None
    if t is not None:
        return "table", t
    return "text", vc.getString().split("\n")


def dialog(win):
    m = win.engine.model
    vc = docapi.view_cursor(m)
    kind, data = _rows(m)
    if kind == "text" and vc.isCollapsed():
        # the paragraph's whole list / the whole document, as the original
        c = vc.getText().createTextCursor()
        c.gotoStart(False)
        c.gotoEnd(True)
        docapi.controller(m).select(c)
        vc = docapi.view_cursor(m)
        data = vc.getString().split("\n")
    opts = {"sep": "\t", "columns_only": False, "case": False}
    d = FDialog(win, "Sort")
    header = Gtk.RadioButton.new_with_mnemonic(None, "Hea_der row")
    noheader = Gtk.RadioButton.new_with_mnemonic_from_widget(header, "No header ro_w")
    noheader.set_active(True)

    def field_names():
        if kind == "table":
            n = data.getColumns().getCount()
            if header.get_active():
                names = []
                for i in range(n):
                    try:
                        names.append(data.getCellByPosition(i, 0).getString().strip() or
                                     "Column %d" % (i + 1))
                    except Exception:
                        names.append("Column %d" % (i + 1))
                return names
            return ["Column %d" % (i + 1) for i in range(n)]
        n = max([len(p.split(opts["sep"])) for p in data if p] or [1])
        if header.get_active() and data:
            first = data[0].split(opts["sep"])
            return [(first[i].strip() if i < len(first) and first[i].strip() else
                     "Field %d" % (i + 1)) for i in range(n)]
        return ["Paragraphs"] + (["Field %d" % (i + 1) for i in range(n)] if n > 1 else [])

    rows = []
    g = Gtk.Grid(column_spacing=8, row_spacing=4)
    for r, title in enumerate(("_Sort by", "_Then by", "Then _by")):
        by = Gtk.ComboBoxText()
        typ = combo([n for n, _v in TYPES], 0)
        using = combo(["Paragraphs"], 0)
        asc = Gtk.RadioButton.new_with_mnemonic(None, "_Ascending")
        desc = Gtk.RadioButton.new_with_mnemonic_from_widget(asc, "_Descending")
        g.attach(Gtk.Label(label=title, xalign=0, use_underline=True), 0, r * 3, 4, 1)
        g.attach(by, 0, r * 3 + 1, 1, 1)
        g.attach(Gtk.Label(label="Type:", xalign=1), 1, r * 3 + 1, 1, 1)
        g.attach(typ, 2, r * 3 + 1, 1, 1)
        g.attach(asc, 3, r * 3 + 1, 1, 1)
        g.attach(Gtk.Label(label="Using:", xalign=1), 1, r * 3 + 2, 1, 1)
        g.attach(using, 2, r * 3 + 2, 1, 1)
        g.attach(desc, 3, r * 3 + 2, 1, 1)
        rows.append((by, typ, using, asc, desc))

    def fill(*_):
        names = field_names()
        for i, (by, typ, using, asc, desc) in enumerate(rows):
            cur = by.get_active()
            by.remove_all()
            if i > 0:
                by.append_text("(none)")
            for n in names:
                by.append_text(n)
            by.set_active(cur if 0 <= cur < len(names) + (1 if i else 0) else 0)
            for w in (typ, using, asc, desc):
                w.set_sensitive(i == 0 or by.get_active() > 0)
    for i, (by, typ, using, asc, desc) in enumerate(rows):
        by.connect("changed", lambda c, i=i: [w.set_sensitive(i == 0 or c.get_active() > 0)
                                               for w in rows[i][1:]])
    d.add(g)
    d.add(heading("My list has"))
    hb = Gtk.Box(spacing=20)
    hb.pack_start(header, False, False, 0)
    hb.pack_start(noheader, False, False, 0)
    d.add(hb)
    header.connect("toggled", fill)
    fill()
    opt_btn = d.add_button("_Options...", 2)
    opt_btn.set_use_underline(True)
    d.get_action_area().reorder_child(opt_btn, 0)
    d.show_all()
    while True:
        r = d.run()
        if r == 2:
            _options(d, opts, kind)
            fill()
            continue
        break
    if r == Gtk.ResponseType.OK:
        keys = []
        for i, (by, typ, using, asc, desc) in enumerate(rows):
            idx = by.get_active() - (1 if i else 0)
            if idx < 0:
                continue
            field = idx + 1
            if kind == "text" and by.get_active_text() == "Paragraphs":
                field = 1
            elif kind == "text" and field_names()[0] == "Paragraphs":
                field = idx          # 'Field n' after 'Paragraphs'
            keys.append((max(1, field), TYPES[max(0, typ.get_active())][1],
                         asc.get_active()))
        if keys:
            ok = sort(m, kind, data, keys, header.get_active(), opts)
            if not ok:
                win.dialogs.message("The selection couldn't be sorted.")
    d.destroy()
    win.focus_document()


def _options(parent, opts, kind):
    d = FDialog(parent, "Sort Options")
    d.add(heading("Separate fields at"))
    tabs = Gtk.RadioButton.new_with_mnemonic(None, "_Tabs")
    commas = Gtk.RadioButton.new_with_mnemonic_from_widget(tabs, "_Commas")
    other = Gtk.RadioButton.new_with_mnemonic_from_widget(tabs, "_Other:")
    oe = Gtk.Entry(max_length=1, width_chars=3)
    {"\t": tabs, ",": commas}.get(opts["sep"], other).set_active(True)
    if opts["sep"] not in ("\t", ","):
        oe.set_text(opts["sep"])
    hb = Gtk.Box(spacing=12)
    for w in (tabs, commas, other, oe):
        hb.pack_start(w, False, False, 0)
    d.add(hb)
    hb.set_sensitive(kind == "text")
    d.add(heading("Sort options"))
    col = Gtk.CheckButton.new_with_mnemonic("Sort column _only")
    col.set_active(opts["columns_only"])
    case = Gtk.CheckButton.new_with_mnemonic("Case _sensitive")
    case.set_active(opts["case"])
    d.add(col)
    d.add(case)
    d.add(heading("Sorting language"))
    lang = combo([n for n, _l, _c in docapi.LANGUAGES], 0)
    d.add(lang)
    d.show_all()
    if d.ask() == Gtk.ResponseType.OK:
        opts["sep"] = "\t" if tabs.get_active() else "," if commas.get_active() else \
            (oe.get_text() or "\t")
        opts["columns_only"] = col.get_active()
        opts["case"] = case.get_active()
        _n, l, c = docapi.LANGUAGES[max(0, lang.get_active())]
        opts["locale"] = (l, c)
    d.destroy()


def _fields(keys, case, locale, template=None):
    out = []
    for field, ftype, ascending in keys[:3]:
        f = bridge.struct("com.sun.star.table.TableSortField")
        if template is not None:
            f.CollatorLocale = template.CollatorLocale
            f.CollatorAlgorithm = template.CollatorAlgorithm
        f.Field = field
        f.IsAscending = ascending
        f.IsCaseSensitive = bool(case)
        f.FieldType = bridge.enum("com.sun.star.table.TableSortFieldType",
                                  {1: "NUMERIC", 2: "ALPHANUMERIC"}.get(ftype, "AUTOMATIC"))
        if locale:
            f.CollatorLocale = bridge.struct("com.sun.star.lang.Locale",
                                             Language=locale[0], Country=locale[1])
        out.append(f)
    return tuple(out)


def sort(m, kind, data, keys, header, opts):
    um = m.getUndoManager()
    um.enterUndoContext("Sort")
    try:
        def fields_for(desc):
            tmpl = None
            for p in desc:
                if p.Name == "SortFields" and p.Value:
                    tmpl = p.Value[0]
            return _fields(keys, opts.get("case"), opts.get("locale"), tmpl)
        if kind == "table":
            t = data
            nr, nc = t.getRows().getCount(), t.getColumns().getCount()
            first = 1 if header else 0
            if nr - first < 2:
                return True
            end = _col_name(nc - 1) + str(nr)
            rng = t.getCellRangeByName("A%d:%s" % (first + 1, end))
            desc = list(rng.createSortDescriptor())
            fields = fields_for(desc)
            out = []
            for p in desc:
                if p.Name == "SortFields":
                    p.Value = uno.Any("[]com.sun.star.table.TableSortField", fields)
                elif p.Name == "IsSortColumns":
                    p.Value = False
                elif p.Name == "ContainsHeader":
                    p.Value = False
                out.append(p)
            uno.invoke(rng, "sort", (tuple(out),))
            return True
        vc = docapi.view_cursor(m)
        rng = vc.getText().createTextCursorByRange(vc.getStart())
        rng.gotoRange(vc.getEnd(), True)
        if header:
            start = vc.getText().createTextCursorByRange(vc.getStart())
            start.gotoNextParagraph(False)
            rng = vc.getText().createTextCursorByRange(start)
            rng.gotoRange(vc.getEnd(), True)
        desc = list(rng.createSortDescriptor())
        fields = fields_for(desc)
        out = []
        for p in desc:
            if p.Name == "SortFields":
                p.Value = uno.Any("[]com.sun.star.table.TableSortField", fields)
            elif p.Name == "IsSortInTable":
                p.Value = False
            elif p.Name == "Delimiter":
                p.Value = uno.Any("char", uno.Char(opts.get("sep", "\t")[:1] or "\t"))
            out.append(p)
        uno.invoke(rng, "sort", (tuple(out),))
        return True
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False
    finally:
        um.leaveUndoContext()


def _col_name(i):
    s = ""
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s
