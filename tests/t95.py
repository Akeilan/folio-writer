exec(open("/home/claude/folio2/tests/common.py").read())
from folio import docapi
A = win.actions; m = lambda: win.engine.model
def s0():
    win.unmaximize(); win.resize(1590,960); win.move(0,0)
    for st, tx in (("Heading 1","Chapter One"),("Normal","Body of chapter one. "*8),("Heading 2","Section 1.1"),("Normal","Body of section."),("Heading 1","Chapter Two"),("Normal","Body two.")):
        A.apply_style(st); A.insert_text(tx); win.engine.command(".uno:InsertPara")
def s1(): win.run("outline-view")
def s2():
    ov = win.outline(); log("rows", len(ov.store))
    ov.tv.get_selection().select_path(Gtk.TreePath.new_from_string("1"))  # Chapter Two
    ov.move(-1)
def s3():
    log("order", [h[1] for h in docapi.headings(m())])
    shot("outline")
def s4(): win.run("close-outline")
def s5(): win.run("immersive-reader")
def s6():
    v = win.immersive(); v.color = ("Sepia", "#f5ecd8", "#3b2f1e"); v.focus_lines = 3; v.spacing=True; v.syllables=True; v.load()
def s7(): shot("immersive"); win.run("read-aloud")
def s8(): log("ra", win.read_aloud.playing, win.read_aloud.speaker.client is not None, win.read_aloud.speaker.espeak); shot("readaloud")
def s9(): win.read_aloud.stop(); app.quit()
steps(s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, delay=1800)
