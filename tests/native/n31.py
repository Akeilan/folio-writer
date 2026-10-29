import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
# 2.31: comments typed in a balloon in the margin, as in Word (W2-03)
from gi.repository import Gtk


def texts():
    return [(c["text"], c["parent"]) for c in E.ed.comments()]


def a():
    yield 1.0
    focus(); yield 0.2
    fresh(); yield 0.2
    T("Some text to comment on"); yield 0.3
    K("ctrl+shift+Left"); yield 0.2
    m = win.comments
    no_dialogs = len([w for w in Gtk.Window.list_toplevels() if w.get_visible()])
    K("ctrl+alt+m"); yield 1.0
    check("Ctrl+Alt+M opens a balloon to type in", m.editing is not None and m.editing["mode"] == "new", m.editing)
    check("no dialog", len([w for w in Gtk.Window.list_toplevels() if w.get_visible()]) == no_dialogs)
    tv = m._editor
    check("the balloon has the keyboard", tv is not None and tv.has_focus(), tv)
    check("comment is in the document already", len(E.ed.comments()) == 1, texts())
    shot("n31_typing"); yield 0.2
    T("Hello comment"); yield 0.6
    K("Escape"); yield 0.8
    check("Escape posts it", texts() == [("Hello comment", None)], texts())
    check("back in the document", E.view.has_focus(), win.get_focus())
    check("balloon shows the text", any("Hello comment" in str([c.get_label() for c in _labels(card)])
                                        for card in m.cards.values()), list(m.comments.values()))
    # ---- reply in place
    cid = list(m.comments.keys())[0]
    m.reply(cid); yield 0.8
    check("reply box open", m.editing and m.editing["mode"] == "reply" and m._editor.has_focus(), m.editing)
    T("A reply"); yield 0.4
    K("ctrl+Return"); yield 0.8
    check("Ctrl+Enter posts the reply", ("A reply", texts()[0][1]) in texts() or len(texts()) == 2, texts())
    check("reply is threaded", any(p is not None for _t, p in texts()), texts())
    # ---- edit in place
    m.edit(cid); yield 0.8
    check("edit box holds the text", m._editor is not None and m.editing["text"] == "Hello comment", m.editing)
    K("End"); T(" again"); yield 0.4
    E.view.grab_focus(); yield 0.8
    check("clicking back into the document posts the edit", ("Hello comment again", None) in texts(), texts())
    # ---- an empty new comment is discarded
    n = len(texts())
    K("ctrl+alt+m"); yield 0.8
    check("second balloon", m.editing is not None, m.editing)
    K("Escape"); yield 0.8
    check("empty comment discarded", len(texts()) == n, texts())
    # ---- Undo takes the comment away
    shot("n31_done"); yield 0.2
    E.ed.mark_saved()


def _labels(w):
    out = []
    if isinstance(w, Gtk.Label):
        out.append(w)
    if isinstance(w, Gtk.Container):
        for c in w.get_children():
            out.extend(_labels(c))
    return out


run_scenarios(a)
