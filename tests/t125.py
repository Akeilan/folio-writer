import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
from folio import docapi
e = win.engine; m = lambda: e.model
def s0():
    win.app.settings["status_items"] = {"line": True, "column": True}
    win.status.apply_items()
    for i in range(8):
        win.actions.insert_text("Line %d text that is long enough. " % i * 3); e.command(".uno:InsertPara")
def s1():
    vc = docapi.view_cursor(m()); vc.jumpToFirstPage(); vc.jumpToStartOfPage()
    vc.goDown(5, False); vc.goRight(2, False)
    win.status.schedule_metrics()
cc = []
e.view.connect("cursor-changed", lambda v,x,y,w,h: cc.append(y))
def s2():
    cc.clear(); win.status._metrics()
    st["pos"] = docapi.read_cursor(m()).getPosition(); c = docapi.read_cursor(m()); log("pos", st["pos"].Y, e.get(".uno:StatePageNumber"))
st = {}
def s3():
    p = docapi.read_cursor(m()).getPosition()
    log("cursor events during metrics", cc)
    log("status", win.status.line.get_text(), win.status.column.get_text(), "cursor same", (p.X, p.Y) == (st["pos"].X, st["pos"].Y)); app.quit()
steps(s0, s1, s2, s3, delay=2000)
