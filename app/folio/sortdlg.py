"""Sort, as in the original: Sort by / Then by / Then by, each with a type,
a 'Using' part and a direction; a header row; options for the field
separator, column-only sorting, case and language."""
from gi.repository import Gtk

from .widgets import FDialog, combo, heading
from . import modelapi

TYPES = [("Text", 2), ("Number", 1), ("Date", 0)]



class _NativeTable:
    """The table rows Sort works on with the new engine (as the old engine's
    table offers them to the dialog)."""

    def __init__(self, rows):
        self.rows = rows

    def getColumns(self):
        n = max([len(r) for r in self.rows] or [1])
        return type("C", (), {"getCount": lambda _s: n})()

    def getCellByPosition(self, c, r):
        t = self.rows[r][c] if r < len(self.rows) and c < len(self.rows[r]) else ""
        return type("Cell", (), {"getString": lambda _s: t})()


def dialog(win):
    ed = win.engine.ed
    got = ed.sort_items(False) if ed is not None else None
    if not got:
        win.status.flash("Select the paragraphs or table rows to sort.")
        return
    is_table, items = got
    m = None
    kind = "table" if is_table else "text"
    data = _NativeTable(items) if is_table else [it[0] for it in items]
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
                field = 0
            elif kind == "text" and field_names()[0] == "Paragraphs":
                field = idx          # 'Field n' after 'Paragraphs'
            keys.append((field, TYPES[max(0, typ.get_active())][1],
                         asc.get_active()))
        if keys:
            ok = sort_native(win, keys, header.get_active(), opts)
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
    lang = combo([n for n, _l, _c in modelapi.LANGUAGES], 0)
    d.add(lang)
    d.show_all()
    if d.ask() == Gtk.ResponseType.OK:
        opts["sep"] = "\t" if tabs.get_active() else "," if commas.get_active() else \
            (oe.get_text() or "\t")
        opts["columns_only"] = col.get_active()
        opts["case"] = case.get_active()
        _n, l, c = modelapi.LANGUAGES[max(0, lang.get_active())]
        opts["locale"] = (l, c)
    d.destroy()




def _col_name(i):
    s = ""
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


# ---------------------------------------------------------------- new engine
def _number(t):
    import re
    m = re.search(r"-?\d[\d,]*(?:\.\d+)?|-?\.\d+", t)
    if not m:
        return None
    try:
        return float(m.group(0).replace(",", ""))
    except ValueError:
        return None


def _date(t):
    import datetime
    t = t.strip()
    for f in ("%m/%d/%Y", "%m/%d/%y", "%Y-%m-%d", "%d %B %Y", "%B %d, %Y", "%B %d %Y", "%d %b %Y",
              "%b %d, %Y", "%m-%d-%Y", "%d.%m.%Y", "%B %Y", "%m/%d"):
        try:
            return datetime.datetime.strptime(t, f).toordinal()
        except ValueError:
            continue
    return None


def sort_keys(items, kind_table, keys, opts):
    """The order Word gives `items` (rows of cell texts, or [paragraph]) for
    keys [(field: 0 whole paragraph / n, type 2 text / 1 number / 0 date,
    ascending)]: blanks first, then the values; items that aren't numbers or
    dates go after those that are."""
    sep = opts.get("sep", "\t") or "\t"
    case = opts.get("case", False)
    order = list(range(len(items)))

    def field_text(item, field):
        if kind_table:
            return item[field - 1] if 0 < field <= len(item) else ""
        text = item[0] if item else ""
        if field <= 0:
            return text
        parts = text.split(sep)
        return parts[field - 1] if field - 1 < len(parts) else ""

    for field, ftype, ascending in reversed(keys[:3]):
        def k(i, field=field, ftype=ftype):
            t = field_text(items[i], field).strip()
            if not t:
                return (0, 0, "")
            if ftype == 1:
                v = _number(t)
                return (1, v, "") if v is not None else (2, 0, t.casefold())
            if ftype == 0:
                v = _date(t)
                return (1, v, "") if v is not None else (2, 0, t.casefold())
            return (1, 0, t if case else t.casefold())
        order.sort(key=k, reverse=not ascending)
    return order


def sort_native(win, keys, header, opts):
    ed = win.engine.ed
    got = ed.sort_items(header)
    if not got:
        return False
    is_table, items = got
    if len(items) < 2:
        return True
    order = sort_keys(items, is_table, keys, opts)
    if order == list(range(len(items))):
        return True
    ok = ed.sort_apply(order, header)
    if ok:
        win.engine.view.after_edit()
    return ok
