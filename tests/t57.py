exec(open("/home/claude/folio2/tests/common.py").read())
from folio import docapi
A = win.actions; m = lambda: win.engine.model
class Ev: pass
def s0(): A.insert_text("First line of text here. " * 6); A.cmd(".uno:InsertPara"); A.insert_text("Second paragraph.")
def s1():
    r = win.engine.page_rects()[0]
    tx, ty = r[0] + 700, r[1] + 1440 + 120
    px, py = win.engine.twips_to_px(tx, ty)
    hit = win._in_left_margin(px, py); log("hit", hit)
    win._margin_select(hit, 1)
def s2():
    log("line sel", repr(docapi.view_cursor(m()).getString()))
    r = win.engine.page_rects()[0]; px, py = win.engine.twips_to_px(r[0] + 700, r[1] + 1440 + 120)
    win._margin_select(win._in_left_margin(px, py), 2)
def s3(): log("para sel", len(docapi.view_cursor(m()).getString())); app.quit()
steps(s0, s1, s2, s3, delay=2000)
