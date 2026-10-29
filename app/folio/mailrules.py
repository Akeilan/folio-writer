"""Mail merge Rules (Ask, Fill-in, If...Then...Else, Merge Record #, Merge
Sequence #, Next Record, Next Record If, Set Bookmark, Skip Record If), Match
Fields, and Auto Check for Errors."""
import json

from gi.repository import Gtk

from ._lazy import docapi
from .widgets import FDialog, combo, grid
from . import modelapi

PREFIX = "com.sun.star.text.fieldmaster.User."
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
def rules(m):
    if not hasattr(m, "getTextFields") and hasattr(m, "engine"):
        from .native import mailmerge
        return mailmerge.rules(m)
    try:
        r = json.loads(modelapi._doc_setting(m, "MergeRules", "") or "{}")
        return r if isinstance(r, dict) else {}
    except ValueError:
        return {}


def _save(m, r):
    modelapi._set_doc_setting(m, "MergeRules", json.dumps(r))


def matches(m):
    if not hasattr(m, "getTextFields") and hasattr(m, "engine"):
        from .native import mailmerge
        try:
            v = json.loads(mailmerge._docvar(m, "FolioMergeMatch") or "{}")
            return v if isinstance(v, dict) else {}
        except ValueError:
            return {}
    try:
        v = json.loads(modelapi._doc_setting(m, "MergeMatch", "") or "{}")
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


# ------------------------------------------------------------ evaluation
def _num(v):
    try:
        return float(str(v).replace(",", ""))
    except ValueError:
        return None


def condition(rule, record):
    v = str(record.get(rule.get("field", ""), ""))
    op = rule.get("op", "eq")
    target = str(rule.get("value", ""))
    if op == "blank":
        return not v.strip()
    if op == "notblank":
        return bool(v.strip())
    a, b = _num(v), _num(target)
    if a is None or b is None:
        a, b = v.lower(), target.lower()
    return {"eq": a == b, "ne": a != b, "lt": a < b, "gt": a > b, "le": a <= b,
            "ge": a >= b}.get(op, False)


def value(rule, record, ctx):
    """The text a rule shows for a record. ctx: {'record', 'seq', 'answers'}."""
    k = rule["kind"]
    if k == "if":
        return rule.get("then", "") if condition(rule, record) else rule.get("else", "")
    if k == "fillin":
        return ctx.get("answers", {}).get(rule["id"], rule.get("default", ""))
    if k == "record":
        return str(ctx.get("record", 1))
    if k == "seq":
        return str(ctx.get("seq", 1))
    if k == "ref":
        return ctx.get("bookmarks", {}).get(rule.get("name", ""), "")
    return ""


def placeholder(rule):
    k = rule["kind"]
    if k in ("next", "nextif", "skipif"):
        return "«%s»" % LABELS[k]
    if k == "if":
        return rule.get("then", "") or rule.get("else", "")
    if k == "fillin":
        return rule.get("default", "")
    if k == "record":
        return "«Merge Record #»"
    if k == "seq":
        return "«Merge Sequence #»"
    if k == "ref":
        return "«%s»" % rule.get("name", "")
    return ""


def _master(m, rid, content):
    fm = m.getTextFieldMasters()
    full = PREFIX + "MergeRule_" + rid
    if fm.hasByName(full):
        ma = fm.getByName(full)
    else:
        ma = m.createInstance("com.sun.star.text.fieldmaster.User")
        ma.Name = "MergeRule_" + rid
    ma.Content = content
    return ma


def insert_rule(m, rule):
    r = rules(m)
    rid = str(max([int(k) for k in r] + [0]) + 1)
    rule["id"] = rid
    r[rid] = rule
    _save(m, r)
    vc = modelapi.view_cursor(m)
    f = m.createInstance("com.sun.star.text.textfield.User")
    f.attachTextFieldMaster(_master(m, rid, placeholder(rule)))
    vc.getText().insertTextContent(vc, f, False)
    return rid


def preview(m, index, rows):
    """Show the rules' values for record `index` (None = placeholders)."""
    r = rules(m)
    fm = m.getTextFieldMasters()
    ctx = {"record": (index or 0) + 1, "seq": (index or 0) + 1,
           "bookmarks": bookmarks_for(r, rows[index] if rows and index is not None else {}, {})}
    for rid, rule in r.items():
        full = PREFIX + "MergeRule_" + rid
        if not fm.hasByName(full):
            continue
        ma = fm.getByName(full)
        if index is None or not rows:
            ma.Content = placeholder(rule)
        elif rule["kind"] in ("next", "nextif", "skipif", "ask", "set"):
            ma.Content = ""
        else:
            ma.Content = value(rule, rows[max(0, min(index, len(rows) - 1))], ctx)


def bookmarks_for(r, record, answers):
    out = {}
    for rid, rule in r.items():
        if rule["kind"] == "set":
            out[rule["name"]] = rule.get("value", "")
        elif rule["kind"] == "ask":
            out[rule["name"]] = answers.get(rid, rule.get("default", ""))
    return out


def skipped(m, record):
    return any(rule["kind"] == "skipif" and condition(rule, record)
               for rule in rules(m).values())


# ------------------------------------------------------------ merging
def fields_in_order(doc):
    """(field, anchor, master name) for merge and rule fields, in reading order."""
    en = doc.getTextFields().createEnumeration()
    out = []
    while en.hasMoreElements():
        f = en.nextElement()
        try:
            if not f.supportsService("com.sun.star.text.textfield.User"):
                continue
            name = f.getTextFieldMaster().Name
        except Exception:
            continue
        if name.startswith("Merge_") or name.startswith("MergeRule_"):
            out.append((f, f.getAnchor(), name))
    body = doc.getText()

    def key(t):
        a = t[1]
        try:
            if a.getText() == body:
                cur = body.createTextCursor()
                cur.gotoStart(False)
                cur.gotoRange(a.getStart(), True)
                return (0, len(cur.getString()))
        except Exception:
            pass
        return (1, 0)
    out.sort(key=key)
    return out


def unlink(doc, rule_defs, records, ptr, seq, answers, master_name_of):
    """Replace this copy's fields with text; returns how many records it used."""
    cur_rec = 0
    by_master = {}
    fields = fields_in_order(doc)
    from .mailings import _drop_empty_line
    for f, a, name in fields:
        rec = records[min(len(records) - 1, ptr + cur_rec)]
        if name.startswith("MergeRule_"):
            rule = rule_defs.get(name[len("MergeRule_"):], {"kind": ""})
            k = rule.get("kind")
            if k == "next" or (k == "nextif" and condition(rule, rec)):
                if ptr + cur_rec + 1 < len(records):
                    cur_rec += 1
                text_value = ""
            else:
                ctx = {"record": rec.get("__index", ptr + cur_rec + 1), "seq": seq, "answers": answers,
                       "bookmarks": bookmarks_for(rule_defs, rec, answers)}
                text_value = value(rule, rec, ctx)
        else:
            if not by_master:
                by_master.update(master_name_of)
            col = by_master.get(name, name[6:])
            text_value = rec.get(col, "")
        text = a.getText()
        c = text.createTextCursorByRange(a)
        text.removeTextContent(f)
        text.insertString(c, text_value, False)
        if not text_value:
            _drop_empty_line(text, c)
    return cur_rec + 1


def ask_answers(win, m, per_record=None):
    """Prompt for Fill-in and Ask rules (those asked once, or for a record)."""
    from .native import mailmerge
    return mailmerge.ask_answers(win, per_record)


# ------------------------------------------------------------ dialogs
def _cond_rows(cols, rule=None):
    field = combo(cols or [""], (rule or {}).get("field") or 0)
    op = combo([o[0] for o in OPS], 0)
    target = Gtk.Entry(text=(rule or {}).get("value", ""))
    op.connect("changed", lambda *_: target.set_sensitive(OPS[op.get_active()][1] not in
                                                          ("blank", "notblank")))
    return field, op, target


def _native(win):
    return getattr(win.engine, "native", False)


def _insert(win, m, rule):
    if _native(win):
        from .native import mailmerge
        mailmerge.insert_rule(win, rule)
        win.refresh_mailings()
    else:
        win.engine.sync(lambda: (insert_rule(m, rule), win.refresh_mailings()))


def rule_dialog(win, kind):
    from . import mailings as M
    if _native(win):
        from .native import mailmerge as M
        m = win
    else:
        pass
    return


def bookmark_names(m):
    if not hasattr(m, "getTextFields") and hasattr(m, "engine"):
        from .native import mailmerge
        return mailmerge.bookmark_names(m)
    return sorted({rule["name"] for rule in rules(m).values()
                   if rule["kind"] in ("ask", "set") and rule.get("name")})


def insert_ref(win, name):
    if _native(win):
        _insert(win, win, {"kind": "ref", "name": name})
        return
    m = win.engine.model
    win.engine.sync(lambda: (insert_rule(m, {"kind": "ref", "name": name}),
                             win.refresh_mailings()))


def match_fields_dialog(win):
    from . import mailings as M
    if _native(win):
        from .native import mailmerge as M
        m = win
    return


def auto_check_dialog(win):
    """Checking and Reporting Errors."""
    from . import mailings as M
    from .dlg_mail import finish
    if _native(win):
        m = win
    return


def find_errors(m):
    from . import mailings as M
    if not hasattr(m, "getTextFields") and hasattr(m, "engine"):
        from .native import mailmerge as M
    cols, rows, inc = M.recipients(m)
    out = []
    if not rows:
        out.append("The document has no recipient list.")
        return out
    for col in M.merge_masters(m):
        if col not in cols:
            out.append("The merge field «%s» doesn't match a column in the recipient list."
                       % col)
    for rule in rules(m).values():
        if rule.get("field") and rule["field"] not in cols:
            out.append("A %s rule uses the field «%s», which isn't in the recipient list."
                       % (LABELS.get(rule["kind"]) or rule["kind"].upper(), rule["field"]))
    if not any(inc):
        out.append("No recipients are selected.")
    return out
