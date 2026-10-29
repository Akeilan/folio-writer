"""Table dialogs: Split Cells, Convert Text to Table, Table Properties,
borders for the whole table."""
from gi.repository import Gtk

from . import docapi
from .widgets import FDialog, LengthSpin, color_button, combo, grid, heading
from . import modelapi


def _table(m):
    vc = modelapi.view_cursor(m)
    try:
        return vc.TextTable, vc.Cell
    except Exception:
        return None, None


class TableDialogs:
    def split_cells(self):
        m = self._model_or_warn()
        if m is None:
            return
        table, cell = _table(m)
        if table is None:
            self.message("Put the cursor in a table cell first.")
            return
        d = FDialog(self.win, "Split Cells")
        cols = Gtk.SpinButton.new_with_range(1, 63, 1)
        rows = Gtk.SpinButton.new_with_range(1, 99, 1)
        cols.set_value(2)
        rows.set_value(1)
        d.add(grid([["Number of _columns:", cols], ["Number of _rows:", rows]]))
        if d.ask() == Gtk.ResponseType.OK:
            c, r = int(cols.get_value()), int(rows.get_value())
            try:
                if c > 1:
                    cur = table.createCursorByCellName(cell.CellName)
                    cur.splitRange(c - 1, False)
                if r > 1:
                    cur = table.createCursorByCellName(cell.CellName)
                    cur.splitRange(r - 1, True)
            except Exception as e:
                self.message("The cells couldn't be split: %s" % e)
        d.done()

    def split_table(self):
        self.eng.command(".uno:SplitTable", {"Type": ("short", 1)})

    def text_to_table(self):
        m = self._model_or_warn()
        if m is None:
            return
        vc = modelapi.view_cursor(m)
        text = vc.getString()
        if not text.strip():
            self.message("Select the text you want to convert to a table first.")
            return
        lines = [l for l in text.replace("\r", "\n").split("\n")]
        while lines and not lines[-1].strip():
            lines.pop()
        d = FDialog(self.win, "Convert Text to Table")
        d.add(heading("Table size"))
        cols = Gtk.SpinButton.new_with_range(1, 63, 1)
        rows_lab = Gtk.Label(label=str(len(lines)), xalign=0)
        d.add(grid([["Number of _columns:", cols], ["Number of rows:", rows_lab]]))
        d.add(heading("Separate text at"))
        seps = {}
        grp = None
        box = Gtk.Box(spacing=12)
        for key, label in (("para", "_Paragraphs"), ("comma", "Co_mmas"), ("tab", "_Tabs"),
                           ("other", "_Other:")):
            rb = Gtk.RadioButton.new_with_mnemonic_from_widget(grp, label)
            grp = grp or rb
            seps[key] = rb
            box.pack_start(rb, False, False, 0)
        other = Gtk.Entry(text="-")
        other.set_width_chars(3)
        box.pack_start(other, False, False, 0)
        d.add(box)

        def sep():
            if seps["comma"].get_active():
                return ","
            if seps["tab"].get_active():
                return "\t"
            if seps["other"].get_active():
                return other.get_text()[:1] or "-"
            return None

        def guess(*_):
            s = sep()
            n = max((len(l.split(s)) for l in lines), default=1) if s else 1
            cols.set_value(n)
        for rb in seps.values():
            rb.connect("toggled", guess)
        (seps["tab"] if any("\t" in l for l in lines) else
         seps["comma"] if all("," in l for l in lines) else seps["para"]).set_active(True)
        guess()
        if d.ask() == Gtk.ResponseType.OK:
            s = sep()
            ncols = int(cols.get_value())
            data = [(l.split(s) if s else [l]) for l in lines]
            vc.setString("")
            table = m.createInstance("com.sun.star.text.TextTable")
            table.initialize(max(1, len(data)), ncols)
            vc.getText().insertTextContent(vc, table, False)
            for r, row in enumerate(data):
                for c in range(ncols):
                    val = row[c].strip() if c < len(row) else ""
                    table.getCellByPosition(c, r).setString(val)
        d.done()


    def table_properties(self, page=0):
        from .tabledraw import properties_dialog
        return properties_dialog(self.win, page)

    def insert_cells(self):
        from .tabledraw import insert_cells_dialog
        insert_cells_dialog(self.win)

    def select_cell(self):
        m = self.model
        if m is None:
            return
        vc = modelapi.view_cursor(m)
        try:
            t, c = vc.TextTable, vc.Cell
            cur = t.createCursorByCellName(c.CellName)
            modelapi.controller(m).select(cur)
        except Exception:
            pass


    # Engine dialogs that slipped through map onto ours
    ENGINE_DIALOGS = {"Split Cells": "split_cells", "Convert Text to Table": "text_to_table",
                      "Split Table": "split_table", "Insert Table": "insert_table_dialog",
                      "Table Properties": "table_properties", "Font": "font_dialog",
                      "Paragraph": "paragraph_dialog", "Find and Replace": "replace",
                      "Insert Bookmark": "bookmark", "Bookmark": "bookmark",
                      "Hyperlink": "hyperlink", "Special Characters": "symbol_dialog",
                      "Word and Character Count": "word_count", "Page Style": "page_setup",
                      "Zoom & View Layout": "zoom_dialog", "Insert Caption": "caption",
                      "Insert Fields": "field_dialog", "Fields": "field_dialog",
                      "Insert Footnote/Endnote": None, "Options": "options"}

    def engine_dialog(self, title):
        target = self.ENGINE_DIALOGS.get(title)
        if target:
            getattr(self, target)()
