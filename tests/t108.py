exec(open("/home/claude/folio2/tests/common.py").read())
from folio import docapi, bridge
A = win.actions; m = lambda: win.engine.model
def s0(): win.unmaximize(); win.resize(1590,960); win.move(0,0); A.insert_text("The zorbliquent widget is here. ")
def s1():
    dl = bridge.create("com.sun.star.linguistic2.DictionaryList")
    log("dicts", [(d.getName(), d.isActive(), str(d.getLocale().Language)) for d in dl.getDictionaries()])
    log("standard", dl.getDictionaryByName("standard.dic"))
    shot("before")
    docapi.add_to_dictionary("zorbliquent")
    log("standard now", [w.getDictionaryWord() for w in bridge.create("com.sun.star.linguistic2.DictionaryList").getDictionaryByName("standard.dic").getEntries()])
def s2(): shot("after"); app.quit()
steps(s0, s1, s2, delay=2500)
