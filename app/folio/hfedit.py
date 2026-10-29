"""Headers and footers the way the original handles them:

* double-click the top or bottom margin of a page to edit the header or
  footer (it is created on the spot if the page has none, without moving
  the body text); double-click the body to go back;
* while you are in one, a single click on the body does nothing, and while
  you are in the body a single click on a header or footer does nothing;
* Link to Previous, Previous / Next section, Show Document Text and the
  Page Number Format dialog on the Header & Footer tab."""
import json

from gi.repository import Gtk

from . import docapi
from .widgets import FDialog, combo, grid
from . import modelapi

MM = 1440.0 / 2540.0       # mm100 -> twips


# ------------------------------------------------------------ geometry
def _page_at(win, tx, ty):
    for i, (rx, ry, rw, rh) in enumerate(win.engine.page_rects()):
        if rx <= tx <= rx + rw and ry <= ty <= ry + rh:
            return i, (rx, ry, rw, rh)
    return None, None


def zone(win, x_px, y_px):
    """'header', 'footer', 'body' or None for a point on the view."""
    return None, None


def press(win, event):
    """Button press on the document. True when it was handled here."""
    from gi.repository import Gdk
    if event.button != 1 or event.state & (Gdk.ModifierType.SHIFT_MASK |
                                           Gdk.ModifierType.CONTROL_MASK):
        return False
    if getattr(win, "multipage", None) is not None:
        return False
    z, info = zone(win, event.x, event.y)
    if z is None:
        return False
    inside = win.in_header_footer()
    double = event.type == Gdk.EventType._2BUTTON_PRESS
    if event.type == Gdk.EventType._3BUTTON_PRESS:
        return inside != (z != "body")
    if z == "body":
        if not inside:
            return False
        if double:
            # back to the body, where the double-click was
            win.engine.click_at(info[2], info[3])
            return True
        return True                 # single clicks on the dimmed body do nothing
    # header / footer zone
    if inside:
        return False                # editing it: clicks work as usual
    if not double:
        return True
    try:
        enter(win, z, info)
    except Exception:
        import traceback
        traceback.print_exc()
    return True


def enter(win, which, info=None):
    """Into the header or footer of the page at info (or the current one)."""
    return


# ------------------------------------------------------------ sections
def section_styles(m):
    """Page styles in document order: one per section."""
    out = []
    try:
        first = m.getText().createTextCursor()
        first.gotoStart(False)
        out.append(first.PageStyleName or "Standard")
    except Exception:
        out.append("Standard")
    en = m.getText().createEnumeration()
    while en.hasMoreElements():
        p = en.nextElement()
        try:
            name = p.PageDescName
        except Exception:
            name = None
        if name and name not in out:
            out.append(name)
    return out


def _style(m, name):
    return m.getStyleFamilies().getByName("PageStyles").getByName(name)


def _linked(m):
    try:
        v = json.loads(modelapi._doc_setting(m, "HFLinks", "") or "{}")
        return v if isinstance(v, dict) else {}
    except ValueError:
        return {}


def which_part(win):
    m = win.engine.model
    try:
        impl = modelapi.read_cursor(m).getText()
        ps = docapi.page_style(m)
        for k in ("Header", "Footer"):
            for suffix in ("Text", "TextFirst", "TextLeft", "TextRight"):
                try:
                    t = getattr(ps, k + suffix)
                except Exception:
                    continue
                if t is not None and t == impl:
                    return k.lower(), suffix
    except Exception:
        pass
    return "header", "Text"


def is_linked(win):
    return False


def _copy_part(win, src, dst, part):
    """Copy one style's header/footer (with formatting) into another's."""
    m = win.engine.model
    key = "Header" if part == "header" else "Footer"
    if not getattr(src, key + "IsOn"):
        return
    if not getattr(dst, key + "IsOn"):
        docapi.enable_header_footer(m, part, dst)
    st, dt = getattr(src, key + "Text"), getattr(dst, key + "Text")
    ctrl = modelapi.controller(m)
    vc = modelapi.view_cursor(m)
    keep = vc.getText().createTextCursorByRange(vc.getStart())
    # in a header/footer, going back by position would land on another page's
    # copy of it: go back to where the caret was on screen instead
    caret = getattr(win, "_follow_rect", None) if win.in_header_footer() else None
    try:
        a = st.createTextCursor()
        a.gotoStart(False)
        a.gotoEnd(True)
        ctrl.select(a)
        t = ctrl.getTransferable()
        b = dt.createTextCursor()
        b.gotoStart(False)
        b.gotoEnd(True)
        b.setString("")
        ctrl.select(b)
        ctrl.insertTransferable(t)
    finally:
        try:
            if caret is not None:
                win.engine.click_at(caret[0] + 1, caret[1] + max(1, caret[3] // 2))
            else:
                vc.gotoRange(keep, False)
        except Exception:
            pass


def set_link(win, on):
    """Link to Previous: this section's header (or footer) is the previous
    section's; turning it on copies it over, and edits are carried along."""
    return


def propagate(win, style_name, part):
    """After editing a header/footer: copy it into the sections linked to it."""
    return


def goto_section(win, d):
    """Previous / Next: the header (or footer) of the neighbouring section."""
    return


# ------------------------------------------------------------ page numbers
FORMATS = [("1, 2, 3, ...", 4), ("a, b, c, ...", 1), ("A, B, C, ...", 0),
           ("i, ii, iii, ...", 3), ("I, II, III, ...", 2)]
SEPARATORS = [("- (hyphen)", "-"), (". (period)", "."), (": (colon)", ":"),
              ("— (em dash)", "—"), ("– (en dash)", "–")]


def _page_fields(m, ps):
    out = []
    for key in ("Header", "Footer"):
        if not getattr(ps, key + "IsOn"):
            continue
        for suffix in ("Text", "TextFirst", "TextLeft"):
            try:
                t = getattr(ps, key + suffix)
            except Exception:
                continue
            if t is None:
                continue
            en = t.createEnumeration()
            while en.hasMoreElements():
                p = en.nextElement()
                try:
                    pe = p.createEnumeration()
                except Exception:
                    continue
                while pe.hasMoreElements():
                    r = pe.nextElement()
                    if getattr(r, "TextPortionType", "") == "TextField":
                        f = r.TextField
                        if f.supportsService("com.sun.star.text.textfield.PageNumber"):
                            out.append((t, r, f))
    return out


def _section_first_para(m, name):
    en = m.getText().createEnumeration()
    first = None
    while en.hasMoreElements():
        p = en.nextElement()
        if not p.supportsService("com.sun.star.text.Paragraph"):
            continue
        if first is None:
            first = p
        try:
            if p.PageDescName == name:
                return p
        except Exception:
            pass
    return first


def format_dialog(win):
    return


def _chapter(m, ps, on, level, separator):
    """Put (or take away) "chapter-separator" in front of each page number."""
    for text, rng, f in _page_fields(m, ps):
        cur = text.createTextCursorByRange(rng.getStart())
        # existing chapter field just before?
        probe = text.createTextCursorByRange(rng.getStart())
        probe.goLeft(2, True)
        has = False
        try:
            en = probe.createEnumeration()
            while en.hasMoreElements():
                p = en.nextElement()
                pe = p.createEnumeration()
                while pe.hasMoreElements():
                    r = pe.nextElement()
                    if getattr(r, "TextPortionType", "") == "TextField" and \
                            r.TextField.supportsService("com.sun.star.text.textfield.Chapter"):
                        has = True
        except Exception:
            pass
        if has and not on:
            probe.setString("")
        elif on and not has:
            c = m.createInstance("com.sun.star.text.textfield.Chapter")
            c.Level = level - 1
            c.ChapterFormat = 1     # number only
            text.insertTextContent(cur, c, False)
            text.insertString(cur, separator, False)


def alignment_tab_dialog(win):
    """Insert Alignment Tab: a tab that lines the text up at the left,
    centre or right of the margin (or indent)."""
    from gi.repository import Gtk
    from .widgets import FDialog, combo, grid, heading
    ed = win.engine.ed
    d = FDialog(win, "Alignment Tab")
    d.add(heading("Alignment"))
    al = Gtk.Box(spacing=12)
    left = Gtk.RadioButton.new_with_mnemonic(None, "_Left")
    center = Gtk.RadioButton.new_with_mnemonic_from_widget(left, "_Center")
    right = Gtk.RadioButton.new_with_mnemonic_from_widget(left, "_Right")
    right.set_active(True)
    for w in (left, center, right):
        al.pack_start(w, False, False, 0)
    d.add(al)
    rel = combo(["Margin", "Indent"], 0)
    d.add(grid([["Ali_gn relative to:", rel]]))
    d.add(heading("Leader"))
    leaders = [("1 None", "none"), ("2 .......", "dot"), ("3 -------", "hyphen"), ("4 ____", "underscore")]
    lead = combo([n for n, _c in leaders], 0)
    d.add(lead)
    if d.ask() == Gtk.ResponseType.OK:
        ps = ed.page_setup(ed.current_section()) or {}
        width = (ps.get("width") or 0) - (ps.get("left") or 0) - (ps.get("right") or 0)
        pv = ed.para_values()
        li = pv.get("ind_left", 0) if rel.get_active() == 1 else 0
        ri = pv.get("ind_right", 0) if rel.get_active() == 1 else 0
        if left.get_active():
            pos, kind = 0, "left"
        elif center.get_active():
            pos, kind = (width - li - ri) // 2, "center"
        else:
            pos, kind = width - li - ri - 1, "right"
        stops = [t for t in pv.get("tabs") or [] if abs(t[0] - pos) > 6]
        stops.append((int(pos), kind, leaders[max(0, lead.get_active())][1]))
        ed.begin_group("Alignment Tab")
        try:
            ed.set_tabs(sorted(stops))
            ed.type_text("\t")
        finally:
            ed.end_group()
        win.engine.view.after_edit()
    d.done()
