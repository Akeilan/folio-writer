import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
from folio import tablelayout as TL, docapi
A = win.actions; m = lambda: win.engine.model
def s0(): win.unmaximize(); win.resize(1590,960); win.move(0,0); win.dialogs._new_table(4, 3)
def s1():
    for v in ["Name","Qty","Price","pear","3","2.5","apple","10","1.2","fig","7","4"]:
        A.insert_text(v); A.cmd(".uno:GoRight")
def s2():
    vc = docapi.view_cursor(m()); t = m().getTextTables().getByIndex(0); vc.gotoRange(t.getCellByName("A2").getStart(), False)
    log("dbg", t.Width, t.TableColumnRelativeSum, [x.Position for x in t.TableColumnSeparators], t.HoriOrient)
    t,_ = TL.current(m()); log("data", TL.table_text(t))
    TL.sort_table(m(), 0, False, True)
def s3():
    t,_ = TL.current(m()); log("sorted", TL.table_text(t))
    TL.sort_table(m(), 1, True, True, True)
def s4():
    t,_ = TL.current(m()); log("by qty desc", TL.table_text(t))
    # go to last cell of Qty column? add row first
    A.cmd(".uno:GoToEndOfDoc")
def s5():
    vc = docapi.view_cursor(m()); t = m().getTextTables().getByIndex(0)
    vc.gotoRange(t.getCellByName("B4").getStart(), False)
    A.cmd(".uno:InsertRowsAfter")
def s6():
    vc = docapi.view_cursor(m()); t = m().getTextTables().getByIndex(0)
    vc.gotoRange(t.getCellByName("B5").getStart(), False)
    log("default", TL.default_formula(m())); TL.insert_formula(m(), "=SUM(ABOVE)")
def s7():
    t = m().getTextTables().getByIndex(0); log("sum", t.getCellByName("B5").getString(), t.getCellByName("B5").getFormula())
    TL.align_cells(m(), "right", "bottom"); TL.text_direction(m()); log("size", TL.cell_size(m()))
    TL.set_col_width(m(), 3000); TL.set_row_height(m(), 1500); log("repeat", TL.repeat_header(m()))
    TL.set_cell_margins(m(), 100, 100, 300, 300)
def s8():
    log("size2", TL.cell_size(m())); win.select_tab("Table Layout"); shot("tlayout")
def s9(): TL.convert_to_text(m(), "\t")
def s10(): log("text", repr(m().getText().getString()), m().getTextTables().getCount()); app.quit()
steps(s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, delay=2000)
