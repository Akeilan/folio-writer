exec(open("/home/claude/folio2/tests/common.py").read())
from folio import docapi, tablestyles, tabledraw
m = lambda: win.engine.model
st = {}
def s0(): win.unmaximize(); win.resize(1590,960); win.move(0,0); win.actions.insert_text("Tables"); win.engine.command(".uno:InsertPara"); st['t'] = tablestyles.insert_table(m(), 3, 3)
def s1():
    t = st['t']; t.getCellByName("A1").setString("a1"); t.getCellByName("A2").setString("a2"); t.getCellByName("A3").setString("a3")
    tabledraw.shift_cells(t, "A2", down=True); log("shift", [t.getCellByPosition(0,r).getString() for r in range(t.getRows().getCount())])
def s2():
    # draw table mode: split cell B1 with a horizontal line through its middle
    win.table_draw.begin("draw")
    vc = docapi.view_cursor(m()); vc.gotoRange(st['t'].getCellByName("B1").getStart(), False)
    log("cell before", st['t'].getCellNames())
    win.table_draw._split(m(), True)
def s3():
    log("after split", len(st['t'].getCellNames()))
    win.table_draw.begin("erase"); win.table_draw.stop()
    GLib.timeout_add(1200, lambda: (shot("tprops"), [w.response(Gtk.ResponseType.OK) for w in Gtk.Window.list_toplevels() if isinstance(w, Gtk.Dialog) and w.get_visible()], False)[2])
    docapi.view_cursor(m()).gotoRange(st['t'].getCellByName("A1").getStart(), False)
    tabledraw.properties_dialog(win, 1)
def s4(): shot("tables"); log("widths", tabledraw.column_widths(st['t'], 16000)); app.quit()
steps(s0, s1, s2, s3, s4, delay=1800)
