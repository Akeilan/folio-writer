"""The Table of Contents, Index and Table of Figures dialogs, as in the
original: print and web previews, page numbers shown / right-aligned, tab
leader, formats, the Options and Modify buttons."""
from gi.repository import Gtk

from .widgets import FDialog, Preview, combo, grid, heading

LEADERS = [("(none)", ""), ("........", "."), ("--------", "-"), ("________", "_")]
FORMATS = ["From template", "Classic", "Distinctive", "Fancy", "Modern", "Formal", "Simple"]
# format: (level-1 bold, level-1 caps, level-2 italic, leader or None to keep)
FORMAT_STYLE = {"Classic": (True, True, False, ""), "Distinctive": (True, False, True, "."),
                "Fancy": (True, False, False, ""), "Modern": (True, False, False, ""),
                "Formal": (False, True, False, "."), "Simple": (False, False, False, "")}


# ---------------------------------------------------------------- previews
def _print_preview(state, entries):
    def draw(cr, W, H):
        cr.set_source_rgb(1, 1, 1)
        cr.paint()
        cr.select_font_face("Sans")
        y = 18
        for lvl, text, page in entries:
            if lvl > state["levels"]():
                continue
            size = 11 - lvl if lvl else 10
            cr.set_font_size(size)
            bold = state["format"]() in FORMAT_STYLE and FORMAT_STYLE[state["format"]()][0] \
                and lvl == 1
            cr.select_font_face("Sans", 0, 1 if bold else 0)
            x = 8 + 12 * max(0, lvl - 1)
            t = text.upper() if (lvl == 1 and state["format"]() in FORMAT_STYLE and
                                 FORMAT_STYLE[state["format"]()][1]) else text
            cr.set_source_rgb(0.1, 0.1, 0.1)
            cr.move_to(x, y)
            cr.show_text(t)
            tx = x + cr.text_extents(t).x_advance
            if state["pages"]():
                ps = str(page)
                pw = cr.text_extents(ps).x_advance
                if state["right"]():
                    px = W - 10 - pw
                    lead = state["leader"]()
                    if lead:
                        lw = cr.text_extents(lead).x_advance or 3
                        lx = tx + 4
                        while lx + lw < px - 3:
                            cr.move_to(lx, y)
                            cr.show_text(lead)
                            lx += lw
                else:
                    px = tx + 4
                cr.move_to(px, y)
                cr.show_text(ps)
            y += size + 9
    return draw


def _web_preview(state, entries):
    def draw(cr, W, H):
        cr.set_source_rgb(1, 1, 1)
        cr.paint()
        cr.select_font_face("Sans")
        y = 18
        for lvl, text, _page in entries:
            if lvl > state["levels"]():
                continue
            size = 11 - lvl if lvl else 10
            cr.set_font_size(size)
            x = 8 + 12 * max(0, lvl - 1)
            if state["links"]():
                cr.set_source_rgb(0.02, 0.39, 0.76)
            else:
                cr.set_source_rgb(0.1, 0.1, 0.1)
            cr.move_to(x, y)
            cr.show_text(text)
            if state["links"]():
                w = cr.text_extents(text).x_advance
                cr.rectangle(x, y + 1.5, w, 0.8)
                cr.fill()
            y += size + 9
    return draw


def _previews(state, entries, web=True):
    hb = Gtk.Box(spacing=12)
    out = []
    for title, fn in (("Print Pre_view", _print_preview),) + \
            ((("_Web Preview", _web_preview),) if web else ()):
        vb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        lab = Gtk.Label(label=title, xalign=0, use_underline=True)
        vb.pack_start(lab, False, False, 0)
        p = Preview(fn(state, entries), 230, 130)
        fr = Gtk.Frame()
        fr.add(p)
        vb.pack_start(fr, False, False, 0)
        hb.pack_start(vb, True, True, 0)
        out.append(p)
    return hb, out


def _common_controls(show_pages, right, leader, links, web=True):
    pages = Gtk.CheckButton.new_with_mnemonic("_Show page numbers")
    pages.set_active(show_pages)
    ralign = Gtk.CheckButton.new_with_mnemonic("_Right align page numbers")
    ralign.set_active(right)
    lead = combo([n for n, _c in LEADERS],
                 next((i for i, (_n, c) in enumerate(LEADERS) if c == leader), 1))
    hl = Gtk.CheckButton.new_with_mnemonic("_Use hyperlinks instead of page numbers")
    hl.set_active(links)
    return pages, ralign, lead, hl


def _wire(widgets, previews, pages, ralign, lead):
    def refresh(*_):
        ralign.set_sensitive(pages.get_active())
        lead.set_sensitive(pages.get_active() and ralign.get_active())
        for p in previews:
            p.queue_draw()
    for w in widgets:
        sig = "toggled" if isinstance(w, Gtk.ToggleButton) else \
            "value-changed" if isinstance(w, Gtk.SpinButton) else "changed"
        w.connect(sig, refresh)
    refresh()


def _modify_styles(win, names):
    """The Style list of the original's Modify button."""
    d = FDialog(win, "Style", buttons=(("OK", Gtk.ResponseType.OK),
                                       ("Cancel", Gtk.ResponseType.CANCEL)))
    lb = Gtk.ListBox()
    for n in names:
        lb.add(Gtk.Label(label=n, xalign=0, margin=3))
    lb.select_row(lb.get_row_at_index(0))
    sw = Gtk.ScrolledWindow()
    sw.set_size_request(240, 180)
    sw.add(lb)
    hb = Gtk.Box(spacing=8)
    hb.pack_start(sw, True, True, 0)
    mod = Gtk.Button(label="_Modify...", use_underline=True)
    mod.set_valign(Gtk.Align.START)
    hb.pack_start(mod, False, False, 0)
    d.add(Gtk.Label(label="Styles:", xalign=0))
    d.add(hb)

    def go(*_):
        row = lb.get_selected_row()
        if row is not None:
            win.dialogs.modify_style(row.get_child().get_text())
    mod.connect("clicked", go)
    lb.connect("row-activated", go)
    d.ask()
    d.destroy()


def _sample_headings(m=None):
    return [(1, "Heading 1", 1), (2, "Heading 2", 3), (3, "Heading 3", 5)]


