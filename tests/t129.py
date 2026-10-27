exec(open("/home/claude/folio2/tests/common.py").read())
from folio import docapi, hfedit
e = win.engine; m = lambda: e.model
fam = lambda: m().getStyleFamilies().getByName("PageStyles")
def s0():
    win.actions.insert_text("Section one.")
    docapi.insert_header_footer(m(), "header", text="Header A")
def s1():
    win.dialogs.section_break("next-page") if hasattr(win.dialogs, "section_break") else win.run(("section-break", "next-page")); win.actions.insert_text("Section two.")
def s2():
    log("sections", hfedit.section_styles(m()))
    log("s2 header", repr(fam().getByName("Section 1").HeaderText.getString() if fam().getByName("Section 1").HeaderIsOn else None))
    e.command(".uno:JumpToHeader")
def s3():
    log("in hf", win.in_header_footer(), "linked", hfedit.is_linked(win), "style", docapi.read_cursor(m()).PageStyleName)
    hfedit.goto_section(win, -1)
def s4():
    log("after prev: style", docapi.read_cursor(m()).PageStyleName, "in hf", win.in_header_footer())
    win.actions.insert_text(" edited")
def s5():
    e.command(".uno:GoToEndOfDoc") if False else None
    vc = docapi.view_cursor(m()); vc.gotoRange(m().getText().getEnd(), False)
def s5b():
    log("where", getattr(win, "_hf_where", None))
    try:
        pass
    except Exception as ex:
        import traceback; log(traceback.format_exc())
def s6():
    log("in hf", win.in_header_footer(), "s2 header now", repr(fam().getByName("Section 1").HeaderText.getString())); app.quit()
steps(s0, s1, s2, s3, s4, s5, s5b, s6, delay=1500)
