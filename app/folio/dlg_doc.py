"""Find and Replace, Go To, Word Count, Zoom, Page Setup, Watermark and
the other document-level dialogs."""
import os
import re

from gi.repository import GLib, Gtk

from .widgets import (FDialog, LengthSpin, Preview, color_button, combo, combo_text,
                      fmt_len, grid, heading, list_selected, listbox)

PAPER = [("Letter", 21590, 27940), ("Legal", 21590, 35560), ("Executive", 18415, 26670),
         ("A3", 29700, 42000), ("A4", 21000, 29700), ("A5", 14800, 21000),
         ("B5 (JIS)", 18200, 25700), ("Tabloid", 27940, 43180),
         ("Envelope #10", 10477, 24130), ("Envelope DL", 11000, 22000)]

MARGIN_PRESETS = {
    "normal": (2540, 2540, 2540, 2540), "narrow": (1270, 1270, 1270, 1270),
    "moderate": (2540, 2540, 1905, 1905), "wide": (2540, 2540, 5080, 5080),
    "classic": (2540, 2540, 3175, 3175), "mirrored": (2540, 2540, 3175, 2540),
}

SPECIAL_CODES = [("Paragraph Mark", "^p"), ("Tab Character", "^t"), ("Any Character", "^?"),
                 ("Any Digit", "^#"), ("Any Letter", "^$"), ("Caret Character", "^^"),
                 ("Em Dash", "^+"), ("En Dash", "^="), ("Manual Line Break", "^l"),
                 ("Nonbreaking Space", "^s"), ("Optional Hyphen", "^-"),
                 ("White Space", "^w"), ("Find What Text", "^&")]


def special_to_regex(s):
    """Word's ^ codes in a search to a regular expression."""
    codes = {"p": "$", "t": "\\t", "?": ".", "#": "[0-9]", "$": "[A-Za-z]", "^": "\\^",
             "+": "\u2014", "=": "\u2013", "l": "\\n", "s": "\u00a0", "-": "\u00ad",
             "w": "[ \\t\u00a0]+"}
    out, i = [], 0
    while i < len(s):
        ch = s[i]
        if ch == "^" and i + 1 < len(s) and s[i + 1] in codes:
            out.append(codes[s[i + 1]])
            i += 2
            continue
        out.append(re.escape(ch))
        i += 1
    return "".join(out)


def special_to_replacement(s):
    codes = {"p": "\\n", "t": "\\t", "^": "^", "+": "\u2014", "=": "\u2013",
             "l": "\u2028", "s": "\u00a0", "-": "\u00ad", "&": "&"}
    out, i = [], 0
    while i < len(s):
        ch = s[i]
        if ch == "^" and i + 1 < len(s) and s[i + 1] in codes:
            out.append(codes[s[i + 1]])
            i += 2
            continue
        if ch in "\\&$":
            out.append("\\" + ch)
        else:
            out.append(ch)
        i += 1
    return "".join(out)


def set_line_number_starts(m, start=1, each_section=False):
    """Line numbers start at `start`, and again at each section if asked."""
    starts = _section_starts(m)
    text = m.getText()
    for i, r in enumerate(starts):
        try:
            c = text.createTextCursorByRange(r)
            if i == 0:
                c.ParaLineNumberStartValue = start if start != 1 or each_section else 0
            else:
                c.ParaLineNumberStartValue = start if each_section else 0
        except Exception as e:
            print("line numbers:", e)


WATERMARK_NAME = "WordPictureWatermark"


def _header_texts(m, ps):
    out = [ps.HeaderText]
    for attr, cond in (("HeaderTextLeft", not ps.HeaderIsShared),
                       ("HeaderTextFirst", not getattr(ps, "FirstIsShared", True))):
        try:
            if cond:
                out.append(getattr(ps, attr))
        except Exception:
            pass
    return out






def _section_starts(m):
    """Where each section begins: the document start, then every page style
    change (a section break)."""
    out = [m.getText().getStart()]
    en = m.getText().createEnumeration()
    first = True
    while en.hasMoreElements():
        p = en.nextElement()
        try:
            if not first and p.supportsService("com.sun.star.text.Paragraph") and \
                    p.PageDescName:
                out.append(p.getStart())
        except Exception:
            pass
        first = False
    try:
        secs = m.getTextSections()
        for i in range(secs.getCount()):
            a = secs.getByIndex(i).getAnchor()
            if a.getText() == m.getText():
                out.append(a.getStart())
    except Exception:
        pass

    def key(r):
        c = m.getText().createTextCursorByRange(m.getText().getStart())
        c.gotoRange(r, True)
        return len(c.getString())
    try:
        out.sort(key=key)
    except Exception:
        pass
    return out


def _fields(m):
    out = []
    en = m.getTextFields().createEnumeration()
    while en.hasMoreElements():
        f = en.nextElement()
        try:
            if f.supportsService("com.sun.star.text.textfield.Annotation"):
                continue
            if f.getAnchor().getText().getImplementationName() == "SwXHeadFootText":
                continue
            out.append(f)
        except Exception:
            pass

    def key(f):
        try:
            c = m.getText().createTextCursorByRange(m.getText().getStart())
            c.gotoRange(f.getAnchor().getStart(), True)
            return len(c.getString())
        except Exception:
            return 0
    out.sort(key=key)
    return out


FIELD_NAMES = {"PageNumber": "Page", "PageCount": "NumPages", "DateTime": "Date",
               "SetExpression": "Seq", "GetReference": "Ref", "Bookmark": "Ref",
               "Author": "Author", "FileName": "FileName", "DocInfo.Title": "Title",
               "WordCount": "NumWords", "CharacterCount": "NumChars", "URL": "Hyperlink",
               "Input": "Fillin", "Macro": "MacroButton", "JumpEdit": "MacroButton",
               "TableOfContents": "TOC"}


def _field_name(f):
    for svc in f.getSupportedServiceNames():
        if svc.startswith("com.sun.star.text.textfield.") or \
                svc.startswith("com.sun.star.text.TextField."):
            kind = svc.split(".")[-1]
            if kind in ("TextField", "TextContent"):
                continue
            return FIELD_NAMES.get(kind, kind)
    return "Field"


def _comment_authors(m):
    out = []
    en = m.getTextFields().createEnumeration()
    while en.hasMoreElements():
        f = en.nextElement()
        try:
            if f.supportsService("com.sun.star.text.textfield.Annotation"):
                out.append(f.Author)
        except Exception:
            pass
    return out


GOTO_KINDS = ["Page", "Section", "Line", "Bookmark", "Comment", "Footnote", "Endnote",
              "Field", "Table", "Graphic", "Equation", "Object", "Heading"]


class DocDialogs:
    # ====================================================== Find and Replace
    def replace(self):
        self.find_replace(1)

    def goto(self):
        self.find_replace(2)

    def find_replace(self, tab=0, text=None):
        from .native import find
        return find.dialog(self.win, tab, text)

    # ================================================================== Zoom
    def zoom_dialog(self):
        cur = int(round(self.eng.view.get_zoom() * 100))
        d = FDialog(self.win, "Zoom")
        d.add(heading("Zoom to"))
        g = Gtk.Grid(column_spacing=24, row_spacing=4)
        grp = None
        opts = [("200%", 200), ("100%", 100), ("75%", 75), ("Page width", "width"),
                ("Text width", "text"), ("Whole page", "page")]
        radios = []
        for i, (label, val) in enumerate(opts):
            rb = Gtk.RadioButton.new_with_label_from_widget(grp, label)
            grp = grp or rb
            radios.append((rb, val))
            g.attach(rb, i // 3, i % 3, 1, 1)
            if val == cur:
                rb.set_active(True)
        d.add(g)
        many = Gtk.RadioButton.new_with_mnemonic_from_widget(grp, "_Many pages:")
        many_n = [2]
        many_btn = Gtk.MenuButton()
        many_lab = Gtk.Label(label="2 pages")
        many_btn.add(many_lab)
        mpop = Gtk.Popover.new(many_btn)
        mg = Gtk.Grid(column_spacing=2, row_spacing=2)
        mg.set_border_width(6)
        for i in range(8):
            b = Gtk.Button(label="▯")
            b.set_tooltip_text("%d page%s" % (i + 1, "" if i == 0 else "s"))

            def pick(_b, n=i + 1):
                many_n[0] = n
                many_lab.set_text("%d page%s" % (n, "" if n == 1 else "s"))
                many.set_active(True)
                mpop.popdown()
                prev.queue_draw()
            b.connect("clicked", pick)
            mg.attach(b, i % 4, i // 4, 1, 1)
        mg.show_all()
        mpop.add(mg)
        many_btn.set_popover(mpop)
        g.attach(many, 2, 0, 1, 1)
        g.attach(many_btn, 2, 1, 1, 1)
        radios.append((many, "many"))
        pct = Gtk.SpinButton.new_with_range(10, 500, 1)
        pct.set_value(cur)
        d.add(grid([["P_ercent:", pct, Gtk.Label(label="%")]]))

        def pdraw(cr, W, H):
            cr.set_source_rgb(1, 1, 1)
            cr.paint()
            choice = next((v for rb, v in radios if rb.get_active()), None)
            if choice == "many":
                n = many_n[0]
                pw = min((W - 10) / n - 6, (H - 10) * 0.77)
                for i in range(n):
                    x = 5 + i * (pw + 6)
                    cr.set_source_rgb(0.4, 0.4, 0.4)
                    cr.rectangle(x, 5, pw, pw / 0.77)
                    cr.stroke()
                return
            cr.set_source_rgb(0, 0, 0)
            cr.select_font_face("Sans")
            cr.set_font_size(max(4, 11 * pct.get_value() / 100.0))
            cr.move_to(8, H / 2 + 5)
            cr.show_text("AaBbCcDdEeXxYyZz")
        d.add(heading("Preview"))
        prev = Preview(pdraw, 300, 70)
        d.add(prev)
        pct.connect("value-changed", lambda *_: prev.queue_draw())

        def on_rb(rb, val):
            if rb.get_active() and isinstance(val, int):
                pct.set_value(val)
            prev.queue_draw()
        for rb, val in radios:
            rb.connect("toggled", on_rb, val)
        if d.ask() == Gtk.ResponseType.OK:
            choice = next((v for rb, v in radios if rb.get_active()), None)
            if choice == "width":
                self.zoom_page_width()
            elif choice == "text":
                self.zoom_page_width(text=True)
            elif choice == "page":
                self.zoom_one_page()
            elif choice == "many":
                self.zoom_pages(many_n[0])
            else:
                self.win.status.set_zoom(pct.get_value() / 100.0)
        d.done()

    def zoom_100(self):
        self.win.status.set_zoom(1.0)

    def _page_px(self):
        """Page width/height in document pixels at zoom 1.0, and the page setup (1/100 mm)."""
        ed = getattr(self.eng, "ed", None)
        if ed is not None and ed.page_count():
            from .native import pagesetup as NP
            w, h = ed.page_size(0)
            try:
                ps = NP.read(self.win)
            except Exception:
                ps = None
            return w * 96 / 72.0, h * 96 / 72.0, ps
        return 816, 1056, None

    def _single_column(self):
        v = self.eng.view
        if (v.columns > 1 or v.side):
            v.set_page_layout(1)

    def zoom_page_width(self, text=False):
        self._single_column()
        w, h, ps = self._page_px()
        if text and ps:
            w = (ps["width"] - ps["left"] - ps["right"]) / 2540.0 * 96
        avail = self.win.canvas.get_allocation().width - 40
        self.win.status.set_zoom(max(0.1, min(5.0, avail / w)))

    def zoom_one_page(self):
        self._single_column()
        w, h, _ = self._page_px()
        a = self.win.canvas.get_allocation()
        self.win.status.set_zoom(max(0.1, min(5.0, min((a.width - 40) / w, (a.height - 30) / h))))

    def zoom_pages(self, n):
        """n pages in view at once (the engine lays pages out one under
        another, so they are fitted top to bottom)."""
        if n > 1:
            # the new engine puts them side by side
            w, h, _ = self._page_px()
            a = self.win.canvas.get_allocation()
            self.eng.view.set_page_layout(n)
            z = min((a.width - 20 * (n + 1)) / (w * n), (a.height - 30) / h)
            self.win.status.set_zoom(max(0.1, min(5.0, z)))
            return
        self._single_column()
        w, h, _ = self._page_px()
        a = self.win.canvas.get_allocation()
        z = min((a.width - 40) / w, (a.height - 30) / (h * n + 20 * (n - 1)))
        self.win.status.set_zoom(max(0.1, min(5.0, z)))

    def zoom_multiple(self):
        self.win.act_multiple_pages()
        return

    # ============================================================ Page setup
    def page_setup(self, tab=0):
        from . import pagesetup
        pagesetup.dialog(self.win, tab)

    def margins(self, preset):
        from .native import pagesetup as NP
        vals = MARGIN_PRESETS[preset] if isinstance(preset, str) else preset
        NP.margins(self.win, *vals, mirrored=preset == "mirrored")
        return

    def orientation(self, landscape):
        from .native import pagesetup as NP
        NP.orientation(self.win, landscape)
        return

    def paper(self, size):
        from .native import pagesetup as NP
        NP.paper(self.win, size[0], size[1])
        return

    def columns(self, n):
        if n == "more":
            self.page_setup(2)
            return
        from .native import pagesetup as NP
        NP.columns(self.win, int(n))

    # ============================================================== Watermark
    def watermark(self, text):
        ed = self.eng.ed
        if text:
            ed.set_watermark("text", text=text, font="Calibri")
        else:
            ed.set_watermark("none")
        self.eng.view.document_changed()
        return

    def watermark_dialog(self):
        d = FDialog(self.win, "Printed Watermark", buttons=(
            ("OK", Gtk.ResponseType.OK), ("Apply", Gtk.ResponseType.APPLY),
            ("Cancel", Gtk.ResponseType.CANCEL)))
        none = Gtk.RadioButton.new_with_mnemonic(None, "_No watermark")
        picw = Gtk.RadioButton.new_with_mnemonic_from_widget(none, "Pi_cture watermark")
        textw = Gtk.RadioButton.new_with_mnemonic_from_widget(none, "Te_xt watermark")
        textw.set_active(True)
        d.add(none)
        d.add(picw)
        pic_path = [None]
        sel_btn = Gtk.Button(label="Select _Picture...", use_underline=True)
        pic_lab = Gtk.Label(xalign=0)
        pic_lab.set_ellipsize(3)
        pic_lab.set_max_width_chars(30)
        scale = combo(["Auto", "500%", "200%", "150%", "100%", "50%"], 0, entry=True)
        wash = Gtk.CheckButton.new_with_mnemonic("_Washout")
        wash.set_active(True)
        pbody = grid([[sel_btn, pic_lab], ["Sc_ale:", scale, wash]])
        pbody.set_margin_start(20)
        d.add(pbody)

        def pick_pic(*_):
            path = self.pick_file("Insert Picture", ["*.png", "*.jpg", "*.jpeg", "*.gif",
                                                     "*.bmp", "*.svg", "*.tif", "*.tiff"],
                                  "All Pictures")
            if path:
                pic_path[0] = path
                pic_lab.set_text(os.path.basename(path))
                picw.set_active(True)
        sel_btn.connect("clicked", pick_pic)
        picw.connect("toggled", lambda w: pbody.set_sensitive(w.get_active()))
        pbody.set_sensitive(False)
        d.add(textw)
        presets = {
            "English (United States)": ["ASAP", "CONFIDENTIAL", "COPY", "DO NOT COPY", "DRAFT", "ORIGINAL",
                                        "PERSONAL", "SAMPLE", "TOP SECRET", "URGENT"],
            "English (United Kingdom)": ["ASAP", "CONFIDENTIAL", "COPY", "DO NOT COPY", "DRAFT", "ORIGINAL",
                                         "PERSONAL", "SAMPLE", "TOP SECRET", "URGENT"],
            "French (France)": ["BROUILLON", "CONFIDENTIEL", "COPIE", "ÉCHANTILLON", "ORIGINAL", "PERSONNEL",
                                "SECRET", "URGENT"],
            "German (Germany)": ["ENTWURF", "KOPIE", "MUSTER", "NICHT KOPIEREN", "ORIGINAL", "PERSÖNLICH",
                                 "STRENG GEHEIM", "VERTRAULICH", "DRINGEND"],
            "Spanish (Spain)": ["BORRADOR", "CONFIDENCIAL", "COPIA", "MUESTRA", "NO COPIAR", "ORIGINAL",
                                "PERSONAL", "SECRETO", "URGENTE"],
        }
        lang = combo(list(presets), 0)
        text = combo(presets["English (United States)"], "CONFIDENTIAL", entry=True)

        def lang_changed(*_):
            items = presets.get(lang.get_active_text() or "", presets["English (United States)"])
            cur = combo_text(text)
            text.remove_all()
            for t in items:
                text.append_text(t)
            text.get_child().set_text(cur if cur in items else items[0])
        lang.connect("changed", lang_changed)
        dflt_font = "Calibri"
        font = combo(self.eng.fonts() or [dflt_font], dflt_font, entry=True)
        color = color_button(0xC0C0C0)
        semi = Gtk.CheckButton.new_with_mnemonic("S_emitransparent")
        semi.set_active(True)
        diag = Gtk.RadioButton.new_with_mnemonic(None, "_Diagonal")
        horiz = Gtk.RadioButton.new_with_mnemonic_from_widget(diag, "_Horizontal")
        lay = Gtk.Box(spacing=12)
        lay.pack_start(diag, False, False, 0)
        lay.pack_start(horiz, False, False, 0)
        size = combo(["Auto", "36", "40", "44", "48", "54", "60", "66", "72", "80", "90", "96",
                      "105", "120", "144"], 0, entry=True)
        body = grid([["_Language:", lang], ["_Text:", text], ["_Font:", font], ["_Size:", size], ["_Color:", color, semi],
                     ["Layout:", lay]])
        body.set_margin_start(20)
        d.add(body)
        textw.connect("toggled", lambda w: body.set_sensitive(w.get_active()))

        def apply():
            if none.get_active():
                self.watermark("")
                return
            ed = self.eng.ed
            if picw.get_active():
                if not pic_path[0]:
                    return
                st = combo_text(scale).strip().rstrip("%")
                try:
                    k = None if st.lower() == "auto" else float(st) / 100.0
                except ValueError:
                    k = None
                ed.set_watermark("picture", path=pic_path[0], scale=k, washout=wash.get_active())
            else:
                c = color.color if color.color is not None and color.color >= 0 else 0xC0C0C0
                sz = combo_text(size).strip()
                try:
                    sz = None if sz.lower() == "auto" else float(sz)
                except ValueError:
                    sz = None
                ed.set_watermark("text", text=combo_text(text), font=combo_text(font) or "Calibri",
                                 size=sz, color=c, semi=semi.get_active(),
                                 diagonal=not horiz.get_active())
            self.eng.view.document_changed()
            return
        while True:
            r = d.ask()
            if r == Gtk.ResponseType.APPLY:
                apply()
                continue
            if r == Gtk.ResponseType.OK:
                apply()
            break
        d.done()

    def line_numbers_dialog(self):
        m = self._model_or_warn()
        if m is None:
            return
        ln = m.getLineNumberingProperties()
        d = FDialog(self.win, "Line Numbers")
        on = Gtk.CheckButton.new_with_mnemonic("Add _line numbering")
        on.set_active(bool(ln.IsOn))
        d.add(on)
        start = Gtk.SpinButton.new_with_range(1, 9999, 1)
        start.set_value(1)
        dist = LengthSpin(ln.Distance or 635, 0, 25400)
        count = Gtk.SpinButton.new_with_range(1, 100, 1)
        count.set_value(ln.Interval or 1)
        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        body.pack_start(grid([["Start _at:", start], ["From _text:", dist],
                              ["Count _by:", count]]), False, False, 0)
        restart = Gtk.RadioButton.new_with_mnemonic(None, "Restart each _page")
        restart_sec = Gtk.RadioButton.new_with_mnemonic_from_widget(restart,
                                                                    "Restart each _section")
        cont = Gtk.RadioButton.new_with_mnemonic_from_widget(restart, "_Continuous")
        starts = _section_starts(m)
        first_val = 0
        try:
            c = m.getText().createTextCursorByRange(starts[0])
            first_val = c.ParaLineNumberStartValue or 0
        except Exception:
            pass
        sec_mode = False
        if len(starts) > 1:
            try:
                c = m.getText().createTextCursorByRange(starts[1])
                sec_mode = (c.ParaLineNumberStartValue or 0) > 0
            except Exception:
                pass
        if first_val:
            start.set_value(first_val)
        (restart if ln.RestartAtEachPage else restart_sec if sec_mode else cont).set_active(True)
        body.pack_start(Gtk.Label(label="Numbering:", xalign=0), False, False, 0)
        body.pack_start(restart, False, False, 0)
        body.pack_start(restart_sec, False, False, 0)
        body.pack_start(cont, False, False, 0)
        body.set_margin_start(20)
        d.add(body)
        on.connect("toggled", lambda w: body.set_sensitive(w.get_active()))
        body.set_sensitive(on.get_active())
        if d.ask() == Gtk.ResponseType.OK:
            ln.IsOn = on.get_active()
            if on.get_active():
                ln.Distance = dist.mm100
                ln.Interval = int(count.get_value())
                ln.RestartAtEachPage = restart.get_active()
                ln.CountEmptyLines = False
                set_line_number_starts(m, int(start.get_value()), restart_sec.get_active())
        d.done()

    def hyphenation_options(self):
        from .native import layoutopts
        layoutopts.options_dialog(self.win)
        return

    def manual_hyphenation(self):
        from .native import layoutopts
        layoutopts.manual_dialog(self.win)
        return
