exec(open("/home/claude/folio2/tests/common.py").read())
def s0(): app.settings["qat"] = [k for k, *_ in win.QAT_COMMANDS]; win.build_qat()
steps(s0, lambda: (shot("t133"), app.settings.__setitem__("qat", ["save","undo","redo"]), app.save_settings(), app.quit()), delay=2000)
