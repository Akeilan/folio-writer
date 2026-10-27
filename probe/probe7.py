import sys, zipfile, re
sys.path.insert(0,'/home/claude/folio2/app')
from folio.engine import Engine
from gi.repository import Gtk, GLib
eng=Engine('/tmp/folio2-probe-profile')
win=Gtk.Window(); win.set_default_size(900,700); sw=Gtk.ScrolledWindow(); sw.add(eng.view); win.add(sw)
out=open('/tmp/probe7.log','w')
def L(*a): out.write(' '.join(str(x) for x in a)+'\n'); out.flush()
def P(mime,data): return lambda: L('paste',eng.paste_data(mime,data))
def C(cmd,args=None): return lambda: eng.command(cmd,args)
def both(*cmds):
    def f():
        for c,a in cmds: eng.command(c,a)
    return f
CASES=[
 ('pc1', both(('.uno:FillPageStyle',{"FillPageStyle":("short",1)}),('.uno:FillPageColor',{"FillPageColor":("long",0xDDEEFF)})), r'fill-color=.#ddeeff.|ddeeff'),
 ('pc2', both(('.uno:FillPageStyle',{"FillPageStyle":("long",1)}),('.uno:FillPageColor',{"FillPageColor.Color":("long",0xDDEEFF)})), r'fill-color=.#ddeeff.|ddeeff'),
 ('pc3', both(('.uno:FillPageStyle',{"FillStyle":("short",1)}),('.uno:FillPageColor',{"Color":("long",0xDDEEFF)})), r'fill-color=.#ddeeff.|ddeeff'),
 ('pc4', both(('.uno:FillPageStyle',{"FillPageStyle.FillStyle":("short",1)}),('.uno:FillPageColor',{"FillPageColor.Color":("long",0xDDEEFF)})), r'fill-color=.#ddeeff.|ddeeff'),
]
i=[0]
def nextcase():
    if i[0]>=len(CASES): Gtk.main_quit(); return False
    name,fn,pat=CASES[i[0]]; i[0]+=1
    eng.command('.uno:GoToEndOfDoc'); eng.command('.uno:InsertText', {"Text":" probe "})
    try: fn()
    except Exception as e: L(name,'EXC',e)
    def check():
        try:
            p='/tmp/pr7_%s.odt'%name; eng.save_as(p,'odt',keep=False)
            z=zipfile.ZipFile(p); allx=''.join(z.read(n).decode(errors='ignore') for n in z.namelist() if n.endswith('.xml'))
            L(name,'match',re.findall(pat,allx)[:5])
        except Exception as e: L(name,'ERR',repr(e))
        GLib.timeout_add(200,nextcase); return False
    GLib.timeout_add(1300,check); return False
eng.connect('loaded', lambda e,ok: GLib.timeout_add(1200,nextcase))
eng.open(sys.argv[1]); win.show_all(); Gtk.main()
