"""Mail merge Rules (Ask, Fill-in, If...Then...Else, Merge Record #, Merge
Sequence #, Next Record, Next Record If, Set Bookmark, Skip Record If), Match
Fields, and Auto Check for Errors."""
import json

from gi.repository import Gtk

from .widgets import FDialog, combo, grid
from .native import mailmerge as M

OPS = [("Equal to", "eq"), ("Not equal to", "ne"), ("Less than", "lt"),
       ("Greater than", "gt"), ("Less than or equal", "le"),
       ("Greater than or equal", "ge"), ("Is blank", "blank"), ("Is not blank", "notblank")]
LABELS = {"next": "Next Record", "nextif": "Next Record If", "skipif": "Skip Record If",
          "ask": "", "set": "", "record": "Merge Record #", "seq": "Merge Sequence #"}

WORD_FIELDS = ["Courtesy Title", "First Name", "Last Name", "Company", "Address 1",
               "Address 2", "City", "State", "Postal Code", "Country or Region", "Phone",
               "E-mail Address"]
GUESS = {"Courtesy Title": ("Title", "Salutation"),
         "First Name": ("First Name", "FirstName", "Given Name", "First"),
         "Last Name": ("Last Name", "LastName", "Surname", "Family Name", "Last"),
         "Company": ("Company", "Company Name", "Organization"),
         "Address 1": ("Address Line 1", "Address1", "Address", "Street"),
         "Address 2": ("Address Line 2", "Address2"), "City": ("City", "Town"),
         "State": ("State", "Province", "Region"),
         "Postal Code": ("ZIP Code", "Zip", "Postal Code", "Postcode", "ZIP"),
         "Country or Region": ("Country", "Country or Region"),
         "Phone": ("Phone", "Telephone", "Home Phone", "Work Phone"),
         "E-mail Address": ("Email", "E-mail", "Email Address", "E-mail Address")}


# ------------------------------------------------------------ storage
def matches(win):
    """Match Fields: {Word field: column} kept in the document."""
    try:
        v = json.loads(M._docvar(win, "FolioMergeMatch") or "{}")
        return v if isinstance(v, dict) else {}
    except ValueError:
        return {}


def matched_column(m, word_field, cols):
    mm = matches(m)
    if word_field in mm:
        return mm[word_field] or None
    low = {c.lower().replace(" ", "").replace("_", "").replace("-", ""): c for c in cols}
    for n in GUESS.get(word_field, (word_field,)):
        c = low.get(n.lower().replace(" ", "").replace("_", "").replace("-", ""))
        if c:
            return c
    return None


def ask_answers(win, m=None, per_record=None):
    """Prompt for Fill-in and Ask rules (those asked once, or for a record)."""
    return M.ask_answers(win, per_record)


# ------------------------------------------------------------ dialogs
def _cond_rows(cols, rule=None):
    field = combo(cols or [""], (rule or {}).get("field") or 0)
    op = combo([o[0] for o in OPS], 0)
    target = Gtk.Entry(text=(rule or {}).get("value", ""))
    op.connect("changed", lambda *_: target.set_sensitive(OPS[op.get_active()][1] not in
                                                          ("blank", "notblank")))
    return field, op, target


def _insert(win, rule):
    M.insert_rule(win, rule)
    win.refresh_mailings()


def rule_dialog(win, kind):
    if win.engine.ed is None:
        return
    cols = M.recipients(win)[0]
    if kind in ("record", "seq", "next"):
        _insert(win, {"kind": kind})
        return
    titles = {"if": "Insert Word Field: IF", "fillin": "Insert Word Field: Fill-in",
              "ask": "Insert Word Field: Ask", "set": "Insert Word Field: Set",
              "nextif": "Insert Word Field: Next Record If",
              "skipif": "Insert Word Field: Skip Record If"}
    d = FDialog(win, titles[kind])
    rule = {"kind": kind}
    if kind in ("if", "nextif", "skipif"):
        field, op, target = _cond_rows(cols)
        d.add(grid([["Field name:", field], ["Comparison:", op], ["Compare to:", target]]))
        if kind == "if":
            then = Gtk.TextView()
            other = Gtk.TextView()
            for tv in (then, other):
                tv.set_size_request(380, 60)
                tv.set_wrap_mode(Gtk.WrapMode.WORD)
            d.add(Gtk.Label(label="Insert this text:", xalign=0))
            f1 = Gtk.Frame()
            f1.add(then)
            d.add(f1)
            d.add(Gtk.Label(label="Otherwise insert this text:", xalign=0))
            f2 = Gtk.Frame()
            f2.add(other)
            d.add(f2)
    if kind in ("ask", "set"):
        name = Gtk.Entry()
        name.set_placeholder_text("Bookmark")
        d.add(grid([["Bookmark:", name]]))
    if kind in ("ask", "fillin"):
        prompt = Gtk.Entry()
        prompt.set_width_chars(40)
        d.add(grid([["Prompt:", prompt]]))
    if kind in ("ask", "fillin", "set"):
        default = Gtk.Entry()
        d.add(grid([["Default " + ("bookmark text:" if kind != "fillin" else "fill-in text:")
                     if kind != "set" else "Value:", default]]))
    if kind in ("ask", "fillin"):
        once = Gtk.CheckButton(label="Ask once")
        d.add(once)
    if d.ask() != Gtk.ResponseType.OK:
        d.done()
        return
    if kind in ("if", "nextif", "skipif"):
        rule.update({"field": field.get_active_text(), "op": OPS[op.get_active()][1],
                     "value": target.get_text()})
        if kind == "if":
            b1, b2 = then.get_buffer(), other.get_buffer()
            rule["then"] = b1.get_text(*b1.get_bounds(), False)
            rule["else"] = b2.get_text(*b2.get_bounds(), False)
    if kind in ("ask", "set"):
        rule["name"] = name.get_text().strip() or "Bookmark1"
    if kind in ("ask", "fillin"):
        rule["prompt"] = prompt.get_text()
        rule["once"] = once.get_active()
    if kind in ("ask", "fillin", "set"):
        rule["default" if kind != "set" else "value"] = default.get_text()
    d.done()
    if kind == "fillin":
        a = win.dialogs.ask_text("Fill-in", rule["prompt"],
                                 rule.get("default", ""))
        if a is not None:
            rule["default"] = a
    _insert(win, rule)


def bookmark_names(win):
    return M.bookmark_names(win)


def insert_ref(win, name):
    _insert(win, {"kind": "ref", "name": name})


def match_fields_dialog(win):
    m = win
    cols = M.recipients(m)[0]
    if not cols:
        win.dialogs.message("Select a recipient list first.")
        return
    d = FDialog(win, "Match Fields")
    lab = Gtk.Label(xalign=0)
    lab.set_line_wrap(True)
    lab.set_max_width_chars(60)
    lab.set_text("Special features in mail merge make it easy to insert information from "
                  "your recipient list. Use the drop-down lists to choose the column that "
                  "matches each address field.")
    d.add(lab)
    choices = ["(not matched)"] + cols
    rows, widgets = [], {}
    for wf in WORD_FIELDS:
        c = matched_column(m, wf, cols)
        w = combo(choices, c if c in cols else "(not matched)")
        widgets[wf] = w
        rows.append([wf + ":", w])
    sw = Gtk.ScrolledWindow()
    sw.set_size_request(420, 320)
    sw.add(grid(rows))
    d.add(sw, expand=True)
    remember = Gtk.CheckButton(label="Remember this matching for this set of data sources "
                                     "on this computer")
    remember.set_active(True)
    d.add(remember)
    if d.ask() == Gtk.ResponseType.OK:
        mm = {wf: (w.get_active_text() if w.get_active() > 0 else "")
              for wf, w in widgets.items()}
        M._set_docvar(win, "FolioMergeMatch", json.dumps(mm))
    d.done()


def auto_check_dialog(win):
    """Checking and Reporting Errors."""
    from .dlg_mail import finish
    m = win
    d = FDialog(win, "Checking and Reporting Errors")
    r1 = Gtk.RadioButton.new_with_mnemonic(
        None, "_Simulate the merge and report errors in a new document.")
    r2 = Gtk.RadioButton.new_with_mnemonic_from_widget(
        r1, "Complete the merge, _pausing to report each error as it occurs.")
    r3 = Gtk.RadioButton.new_with_mnemonic_from_widget(
        r1, "Complete the merge _without pausing. Report errors in a new document.")
    for r in (r1, r2, r3):
        d.add(r)
    res = d.ask()
    mode = [r1, r2, r3].index(next(r for r in (r1, r2, r3) if r.get_active()))
    d.done()
    if res != Gtk.ResponseType.OK:
        return
    errors = find_errors(m)
    if mode == 1 and errors:
        for e in errors:
            if not win.dialogs.confirm(e + "\n\nContinue?", yes="OK", no="Cancel"):
                return
        finish(win)
        return
    if mode == 0 and not errors:
        win.dialogs.message("No mail merge errors have been found in %s." %
                            (win.doc_name()))
        return
    if errors:
        w = win.app.new_window()

        def fill():
            if w.engine.ed is None:
                return True
            w.actions.insert_text("Mail Merge Errors\n\n" + "\n".join(errors))
            return False
        from gi.repository import GLib
        GLib.timeout_add(800, fill)
    if mode == 2:
        finish(win)


def find_errors(m):
    cols, rows, inc = M.recipients(m)
    out = []
    if not rows:
        out.append("The document has no recipient list.")
        return out
    for col in M.merge_masters(m):
        if col not in cols:
            out.append("The merge field «%s» doesn't match a column in the recipient list."
                       % col)
    for rule in M.rules(m).values():
        if rule.get("field") and rule["field"] not in cols:
            out.append("A %s rule uses the field «%s», which isn't in the recipient list."
                       % (LABELS.get(rule["kind"]) or rule["kind"].upper(), rule["field"]))
    if not any(inc):
        out.append("No recipients are selected.")
    return out
