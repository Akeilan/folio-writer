exec(open("/home/claude/folio2/tests/common.py").read())
import subprocess
def x(*a): subprocess.run(["xdotool"] + list(a), env=dict(os.environ, DISPLAY=":99"))
from folio import docapi
def s0(): win.present(); win.focus_document()
def s1(): x("type", "--delay", "40", "teh cat sat. it was (c) here -- yes \"quoted\" don't 1st ")
def s2(): x("key", "Return"); x("type", "--delay", "40", "* bullet one"); x("key", "Return"); x("type", "--delay","40","second")
def s3(): x("key", "Return", "Return"); x("type", "--delay", "40", "1. num one"); x("key", "Return"); x("type","--delay","40","two")
def s4(): x("key","Return","Return"); x("type","--delay","40","---"); x("key","Return"); x("type","--delay","40","after line :) www.example.com ")
def s5():
    log(repr(win.engine.model.getText().getString())); shot("autocorrect"); app.quit()
steps(s0, s1, s2, s3, s4, s5, delay=4000)
