exec(open("/home/claude/folio2/tests/common.py").read())
from folio import docapi, macros
from folio.customize import catalog
e = win.engine; m = lambda: e.model
st = {}
def find_btn(w, label):
    if isinstance(w, Gtk.Label) and w.get_text() == label: return w
    if isinstance(w, Gtk.Container):
        for c in w.get_children():
            r = find_btn(c, label)
            if r: return r
def s0():
    win.actions.insert_text("make me loud"); e.command(".uno:SelectAll")
    cat = catalog(win); st["key"] = next(k for k in cat if "Change Case" in k)
    log("key", st["key"])
    win.macro_recorder.start("M2")
    pop = cat[st["key"]][2].open_menu(); st["pop"] = pop
def s1():
    lab = find_btn(st["pop"], "UPPERCASE"); b = lab.get_parent()
    while not isinstance(b, Gtk.Button): b = b.get_parent()
    b.clicked()
def s2():
    win.macro_recorder.stop(); log("steps", macros.store(app)["M2"]["steps"], repr(m().getText().getString()))
    e.command(".uno:SelectAll"); e.command(".uno:Delete"); win.actions.insert_text("second text"); e.command(".uno:SelectAll")
def s3(): macros.play(win, "M2")
def s4(): log("replayed", repr(m().getText().getString())); app.quit()
steps(s0, s1, s2, s3, s4, delay=1500)
