exec(open("/home/claude/folio2/tests/common.py").read())
from folio import customize
A = win.actions
def s0():
    win.unmaximize(); win.resize(1590,960); win.move(0,0)
    cat = customize.catalog(win); log("catalog", len(cat), [k for k in list(cat)[:5]])
    app.settings["ribbon_custom"] = {"hidden": ["Draw"], "tabs": [{"name": "My Tools"}],
        "groups": [{"tab": "Home", "name": "Favorites", "commands": ["Insert|Table", "Review|Track Changes"]},
                   {"tab": "My Tools", "name": "Stuff", "commands": ["Home|Bold", "Insert|Page Break", "Review|Read Aloud"]}]}
    app.settings["user_keys"] = {"ctrl+alt+q": "Home|Bold"}
    customize.apply(win); customize.apply_keys(win)
def s1(): shot("custom_home"); win.select_tab("Custom:My Tools") if False else win.ribbon.select(win.ribbon.tab_by_name("Custom:My Tools"))
def s2():
    shot("custom_tab"); A.insert_text("abc"); win.engine.command(".uno:SelectAll")
    import subprocess; subprocess.run(["xdotool","key","ctrl+alt+q"])
def s3():
    log("bold", win.engine.get(".uno:Bold"))
    GLib.timeout_add(1500, lambda: (shot("opts"), [w.response(Gtk.ResponseType.CANCEL) for w in Gtk.Window.list_toplevels() if isinstance(w, Gtk.Dialog) and w.get_visible()], False)[2])
    win.dialogs.options("Customize Ribbon")
def s4():
    app.settings["ribbon_custom"] = {}; app.settings["user_keys"] = {}; app.quit()
steps(s0, s1, s2, s3, s4, delay=1800)
