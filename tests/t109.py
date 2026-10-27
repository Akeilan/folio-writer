exec(open("/home/claude/folio2/tests/common.py").read())
from folio import docapi
A = win.actions
import os
def s0(): win.unmaximize(); win.resize(1590,960); win.move(0,0); A.insert_text("The zorbliquent widget is here, flimbersnatch too. ")
def s1():
    if os.environ.get("PASS2") is None:
        docapi.add_to_dictionary("zorbliquent"); win.dialogs._ignore_word("flimbersnatch")
def s2(): shot("dict_" + (os.environ.get("PASS2") or "1")); log("file", docapi.user_words()); app.quit()
steps(s0, s1, s2, delay=2500)
