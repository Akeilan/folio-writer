import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
from folio import docapi, macros, trackoptions
e = win.engine; m = lambda: e.model
def key(*k): return lambda: subprocess.run(["xdotool", "key", "--delay", "60"] + list(k))
def typ(t): return lambda: subprocess.run(["xdotool", "type", "--delay", "40", t])
def s0(): win.focus_document(); win.macro_recorder.start("M1")
def s9():
    win.macro_recorder.stop(); log("steps", macros.store(app)["M1"]["steps"])
    e.command(".uno:SelectAll"); e.command(".uno:Delete")
def s10(): macros.play(win, "M1")
def s11():
    log("replayed text", repr(m().getText().getString()))
    # tracking options apply
    o = trackoptions.options(app); o["ins_mark"] = 1; app.settings["track_options"] = o; trackoptions.apply(win)
    # opentype font name
    vc = docapi.view_cursor(m()); vc.gotoStart(False); vc.gotoEnd(True); vc.CharFontName = "Carlito:onum&tnum"
    log("font", docapi.read_cursor(m()).CharFontName)
def s12():
    w2 = app.new_window(); st["w2"] = w2
def s13():
    win.act_side_by_side(); log("partner", win.side_partner is st["w2"], "sync", win._sync_ids is not None)
def s13b(): shot("t131sbs")
def s14():
    win.act_side_by_side(); log("ended", win.side_partner); app.quit()
st = {}
steps(s0, typ("Hello "), key("ctrl+b"), typ("bold"), key("ctrl+b"), key("Return"), typ("Line2"), key("Home"), lambda: None, s9, s10, s11, s12, s13, s13b, s14, delay=1200)
