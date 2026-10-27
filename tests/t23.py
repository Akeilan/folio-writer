exec(open("/home/claude/folio2/tests/common.py").read())
import subprocess
def x(*a): subprocess.run(["xdotool"] + list(a), env=dict(os.environ, DISPLAY=":99"))
def s0(): win.unmaximize(); win.resize(1590, 960); win.move(0,0)
def s1(): win.actions.insert_text("Paragraph one with enough words to wrap across the line so that the indent markers show how they work in practice, just like in the reference program.")
def s2(): shot("ruler1"); win.actions.do_hanging_indent()
def s3():
    shot("ruler2"); rs = win.ruler_state; log("ps", {k: rs["page"][k] for k in ("width","left","right","top")}, "ind", rs.get("indents"), "raw", win.engine.get(".uno:LeftRightParaMargin"), "rects", win.engine.page_rects()[:1], "zoom", win.engine.view.get_zoom()); app.quit()
steps(s0, s1, s2, s3, delay=1800)
