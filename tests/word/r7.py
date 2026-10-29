import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
from folio.readmode import ReadMode
def d():
    win.open_file("/tmp/wfid/fid.docx"); yield 5.0
    rib("View", "Read Mode"); yield 2.0
    rm = win.alt_view
    check("read mode open", isinstance(rm, ReadMode) and not win.ribbon.get_visible(), type(rm).__name__)
    shot("r7_a")
    K("Right"); yield 1.0
    check("Right turns screen", rm.first == 2, (rm.first, rm.where.get_text()))
    shot("r7_b")
    rm.set_color("sepia"); yield 0.8
    shot("r7_sepia")
    rm.set_color("none")
    K("Escape"); yield 1.0
    check("Esc returns to editing", win.alt_view is None and win.ribbon.get_visible() and win.status.get_visible(), "")
run_scenarios(d)
