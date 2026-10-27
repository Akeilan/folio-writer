exec(open("/home/claude/folio2/tests/common.py").read())
def s0():
    out = sorted({(c.tooltip_text or "") for c in win.ribbon.all_controls()})
    log(len(out)); log(" | ".join(out)); app.quit()
steps(s0, delay=1000)
