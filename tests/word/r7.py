exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
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
