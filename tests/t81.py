exec(open("/home/claude/folio2/tests/common.py").read())
import os, subprocess
from folio import docprotect
A = win.actions; m = lambda: win.engine.model
P = "/tmp/ftest_final.docx"
def s0():
    win.unmaximize(); win.resize(1590,960); win.move(0,0)
    A.insert_text("Final doc text"); win.save_to(P)
def s1():
    A.insert_text(" more"); docprotect.keep_version(app, win); log("vers", len(docprotect.versions(app, P)))
def s2(): app.toggle_pin(P); win.show_backstage(); 
def s3(): shot("bs_home")
def s4(): win.backstage.nav("info")
def s5(): shot("bs_info")
def s6():
    win.backstage.close()
    win.dialogs.confirm = lambda *a, **k: True; win.dialogs.message = lambda *a, **k: None
    docprotect.mark_final(win, True); log("ro", win.read_only, win.msgbar.kind)
def s7(): shot("final")
def s8():
    fd = {"PageRange": "1", "UseTaggedPDF": True, "ExportBookmarks": True}
    log("pdf", win.engine.save_as("/tmp/o.pdf", "pdf", keep=False, filter_data=fd))
    v = docprotect.versions(app, P)[0]; st['w'] = docprotect.open_version(win, *v)
def s9(): shot("version")
def s10(): app.toggle_pin(P); app.quit()
st = {}
steps(s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, delay=1800)
