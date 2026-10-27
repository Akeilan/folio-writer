exec(open("/home/claude/folio2/tests/common.py").read())
e = win.engine
def close_dialogs(name):
    def f():
        shot(name)
        for w in Gtk.Window.list_toplevels():
            if isinstance(w, Gtk.Dialog) and w.get_visible():
                w.response(Gtk.ResponseType.CANCEL)
        return False
    return f
def dlg(name, fn, wait=1500):
    def s():
        GLib.timeout_add(wait, close_dialogs(name))
        fn()
    s.__name__ = name
    return s
def s0():
    e.command(".uno:InsertText", {"Text": "Sample text for the dialogs. "})
    e.command(".uno:SelectAll")
def bs_home(): win.show_backstage("home")
def bs_shot(): shot("bs_home"); win.backstage.nav("info")
def bs_info(): shot("bs_info"); win.backstage.nav("print")
def bs_print(): shot("bs_print"); win.backstage.nav("saveas")
def bs_saveas(): shot("bs_saveas"); win.backstage.close()
def tab_insert(): win.ribbon.select(win.ribbon.tab_by_name("Insert"))
def tab_insert_shot(): shot("tab_insert"); win.ribbon.select(win.ribbon.tab_by_name("Layout"))
def tab_layout_shot(): shot("tab_layout"); win.ribbon.select(win.ribbon.tab_by_name("References"))
def tab_ref_shot(): shot("tab_refs"); win.ribbon.select(win.ribbon.tab_by_name("Design"))
def tab_design_shot(): shot("tab_design"); win.ribbon.select(win.ribbon.tab_by_name("Home"))
def keytips(): win.keytips.start()
def keytips_shot(): shot("keytips"); win.keytips.leave()
def nav(): win.dialogs.find_pane("text")
def nav_shot(): shot("navpane"); win.dialogs.styles_pane()
def styles_shot(): shot("stylespane"); win.dialogs.spelling()
def editor_shot(): shot("editorpane")
steps(s0,
      dlg("font", win.dialogs.font_dialog),
      dlg("para", win.dialogs.paragraph_dialog),
      dlg("pagesetup", win.dialogs.page_setup),
      dlg("symbol", win.dialogs.symbol_dialog),
      dlg("hyperlink", win.dialogs.hyperlink),
      dlg("wordcount", win.dialogs.word_count),
      bs_home, bs_shot, bs_info, bs_print, bs_saveas,
      tab_insert, tab_insert_shot, tab_layout_shot, tab_ref_shot, tab_design_shot,
      keytips, keytips_shot, nav, nav_shot, styles_shot, editor_shot,
      lambda: app.quit(), delay=2200)
