import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
def s0(): win.actions.insert_text("Mispeled wrod here. ")
def s1(): log("spell on", win.engine.is_on(".uno:SpellOnline")); app.settings["auto_spell"] = False; app.settings["screentips"] = False; app.settings["units"] = "Millimeters"; app.apply_settings()
def s2():
    from folio.widgets import fmt_len
    log("spell on", win.engine.is_on(".uno:SpellOnline"), "tips", win.ribbon.all_controls()[5].get_has_tooltip(), fmt_len(2540))
    app.settings["auto_spell"] = True; app.settings["screentips"] = True; app.settings.pop("units"); app.apply_settings()
def s3(): log("spell on", win.engine.is_on(".uno:SpellOnline")); win.dialogs.options() if hasattr(win.dialogs,'options') else None
def s4(): pass
steps(s0, s1, s2, s3, delay=2000)
def closer():
    for w in Gtk.Window.list_toplevels():
        if isinstance(w, Gtk.Dialog) and w.get_visible():
            shot("options"); w.response(Gtk.ResponseType.CANCEL); GLib.timeout_add(500, app.quit); return False
    return True
GLib.timeout_add(9000, closer)
