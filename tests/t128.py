exec(open("/home/claude/folio2/tests/common.py").read())
def s0(): win.actions.insert_text("Green theme check.")
def s1(): shot("t128a"); win.run("backstage-open") if False else win.backstage.open() if hasattr(win.backstage,"open") else None
def s2(): shot("t128b"); app.quit()
steps(s0, s1, s2, delay=2000)
