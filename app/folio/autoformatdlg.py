"""AutoFormat (W3-09): the AutoFormat dialog and AutoFormat Now (Ctrl+Alt+K)."""
from gi.repository import Gtk

from .widgets import FDialog, combo

DOC_TYPES = ["General document", "Letter", "Email"]


def _options(win, doc_type="General document"):
    from .native import autoformat as AF
    s = win.app.settings
    o = {k: bool(s.get(k, d)) for k, d in AF.defaults().items()}
    if doc_type == "Letter":
        # a letter's address and closing lines aren't headings
        o["af_headings"] = False
    return o


def _summary(done):
    if not done:
        return "AutoFormat found nothing to change."
    parts = ["%d %s" % (n, k) for k, n in sorted(done.items())]
    return "Formatting completed: " + ", ".join(parts) + "."


def autoformat_now(win, doc_type="General document"):
    from .native import autoformat as AF
    ed = win.engine.ed
    if ed is None or win.read_only:
        return None
    done = AF.run(ed, _options(win, doc_type))
    win.engine.view.after_edit()
    try:
        win.refresh_styles()
    except Exception:
        pass
    return done


def dialog(win):
    d = FDialog(win, "AutoFormat", width=420)
    lab = Gtk.Label(xalign=0)
    lab.set_text("Folio Page will automatically format “%s”." % win.doc_name())
    d.add(lab)
    now = Gtk.RadioButton.new_with_mnemonic(None, "_AutoFormat now")
    review = Gtk.RadioButton.new_with_mnemonic_from_widget(now, "AutoFormat and _review each change")
    d.add(now)
    d.add(review)
    d.add(Gtk.Label(label="Please select a document type to help improve the formatting process:", xalign=0))
    kind = combo(DOC_TYPES, 0)
    d.add(kind)
    opt = Gtk.Button(label="_Options...", use_underline=True)
    opt.set_halign(Gtk.Align.START)

    def options(*_):
        from .options import autocorrect_options
        autocorrect_options(win, tab=3)
    opt.connect("clicked", options)
    d.add(opt)
    r = d.ask()
    doc_type = kind.get_active_text() or DOC_TYPES[0]
    reviewing = review.get_active()
    d.done()
    if r != Gtk.ResponseType.OK:
        return None
    done = autoformat_now(win, doc_type)
    if done is None:
        return None
    if reviewing:
        return review_dialog(win, done)
    return done


def review_dialog(win, done):
    """After AutoFormat and review: keep the changes or take them all back."""
    d = FDialog(win, "AutoFormat", buttons=(("_Accept All", 1), ("_Reject All", 2), ("Cancel", Gtk.ResponseType.CANCEL)))
    lab = Gtk.Label(xalign=0)
    lab.set_line_wrap(True)
    lab.set_max_width_chars(60)
    lab.set_text(_summary(done) + "\n\nYou can now accept or reject all of the changes.")
    d.add(lab)
    for resp in (1, 2):
        b = d.buttons.get(resp)
        if b is not None:
            b.set_use_underline(True)
    r = d.ask()
    d.done()
    if r == 2 and done:
        win.engine.ed.undo()
        win.engine.view.after_edit()
        return {}
    return done
