exec(open("/home/claude/folio2/tests/common.py").read())
from folio import docapi, objecttools
A = win.actions; e = win.engine; m = lambda: e.model
cc = []
e.view.connect("cursor-changed", lambda v,x,y,w,h: cc.append((x,y,w,h)))
st = {}
def s0():
    A.insert_text("Some text before ")
    st["obj"] = docapi.insert_formula(m(), "{a over b} + x^2", display=False)
    A.insert_text(" and after.")
def s1():
    obj = st["obj"]
    log("size mm100", obj.Size.Width, obj.Size.Height, "vc pos", docapi.read_cursor(m()).getPosition())
    vc = docapi.view_cursor(m())
    vc.gotoRange(obj.getAnchor().getStart(), False); cc.clear()
def s2():
    log("caret before", cc[-1:] ); vc = docapi.view_cursor(m()); log("vcpos before", vc.getPosition())
    vc.goRight(1, False); cc.clear()
def s3():
    log("caret after", cc[-1:]); vc = docapi.view_cursor(m()); log("vcpos after", vc.getPosition())
    log("pages", e.page_rects()[:2])
def s4():
    docapi.select_object(m(), st["obj"])
def s5():
    log("after uno select", e.state.get(".uno:Position"), e.state.get(".uno:Size"), objecttools.object_rect(win))
def s6():
    pass
steps(s0, s1, s2, s3, s4, s5, lambda: (shot("t117"), app.quit()), delay=1500)
