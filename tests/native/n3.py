import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
from folio.native.uno_props import CursorProps
from folio.native import values as bridge
def a():
    yield 1.0
    focus(); yield 0.2
    T("Formatting through the dialogs' properties.\nSecond paragraph."); yield 0.4
    K("ctrl+a"); yield 0.2
    vc = CursorProps(E, "Font")
    vc.CharWeight = 150.0
    vc.CharPosture = bridge.enum("com.sun.star.awt.FontSlant", "ITALIC")
    vc.CharHeight = 14
    vc.CharFontName = "Liberation Serif"
    vc.CharColor = 0xC00000
    vc.CharUnderline = 2
    vc.ParaAdjust = 3
    vc.ParaLeftMargin = 1270
    vc.ParaFirstLineIndent = -635
    vc.ParaTopMargin = 423
    ls = bridge.struct("com.sun.star.style.LineSpacing"); ls.Mode = 0; ls.Height = 150
    vc.ParaLineSpacing = ls
    ts = bridge.struct("com.sun.star.style.TabStop"); ts.Position = 2540
    ts.Alignment = bridge.enum("com.sun.star.style.TabAlign", "RIGHT"); ts.FillChar = "."
    vc.ParaTabStops = (ts,)
    yield 0.5
    r, p = E.ed.run_values(), E.ed.para_values()
    check("run props", (r["bold"], r["italic"], r["size"], r["font"], r["color"], r["underline"]) ==
          (True, True, 14.0, "Liberation Serif", 0xC00000, "double"), r)
    check("para props", (p["align"], p["ind_left"], p["ind_first"], p["before"], p["line"], p["tabs"]) ==
          ("center", 720, -360, 240, 360, [(1440, "right", "dot")]), p)
    check("reads back", vc.CharWeight == 150.0 and vc.ParaAdjust == 3 and vc.ParaLeftMargin == 1270,
          (vc.CharWeight, vc.ParaAdjust, vc.ParaLeftMargin))
    check("one undo step", E.ed.state()["undo_name"] == "Font", E.ed.state()["undo_name"])
    K("ctrl+z"); yield 0.4
    r = E.ed.run_values()
    check("undone together", not r["bold"] and r["size"] == 11.0 and E.ed.para_values()["align"] == "left", r)
    # the real dialogs open and close without trouble
    GLib.timeout_add(1200, lambda: (K("Return"), False)[1])
    win.run("font-dialog"); yield 1.5
    GLib.timeout_add(1200, lambda: (K("Return"), False)[1])
    win.run("paragraph-dialog"); yield 1.5
    shot("n3")
    check("alive", True)
run_scenarios(a)
