import sys
sys.path.insert(0,'/home/claude/folio2/app')
from folio.engine import Engine
from folio.eqn import omml
from gi.repository import Gtk, GLib
eng=Engine('/tmp/folio2-probe-profile')
win=Gtk.Window(); win.set_default_size(900,700); sw=Gtk.ScrolledWindow(); sw.add(eng.view); win.add(sw)
out=open('/tmp/probe6.log','w')
def L(*a): out.write(' '.join(str(x) for x in a)+'\n'); out.flush()
steps=[]
def S(f): steps.append(f); return f
@S
def a():
    eng.command('.uno:InsertText', {"Text":"Eq: "})
    L('paste', eng.paste_data('text/rtf', omml.to_rtf("x=(-b±√(b^2-4ac))/2a")))
    eng.command('.uno:InsertText', {"Text":" after"})
@S
def b():
    for _ in range(6): eng.command('.uno:GoLeft')
    eng.command('.uno:CharLeftSel') if False else eng.command('.uno:GoLeft')
@S
def c():
    eng.command('.uno:CharRightSel') if False else None
    eng.command('.uno:GoRight', {"Select":("boolean",True)})
@S
def c2():
    eng.command('.uno:Copy')
@S
def d():
    L('seltype', eng.selection_type())
    r=eng.selection('text/rtf')
    L('rtf has math', omml.has_math(r), len(r))
    L('linear', omml.from_rtf(r))
    L('plain', repr(eng.selection()))
    for m in ['application/x-openoffice-embed-source-xml;windows_formatname="Star Embed Source (XML)"','application/vnd.oasis.opendocument.text','text/html','image/png','application/x-openoffice-objectdescriptor-xml;windows_formatname="Star Object Descriptor (XML)"']:
        r=eng.selection_bytes(m); L('mime',m[:40],len(r), repr(r[:60]))
        if r[:2]==b'PK':
            import zipfile,io; z=zipfile.ZipFile(io.BytesIO(r)); L(z.namelist()); c=z.read('content.xml').decode(); import re; L(re.findall(r'<annotation[^>]*>(.*?)</annotation', c))
@S
def e0():
    eng.command('.uno:Escape') if False else None
    eng.command('.uno:Delete')
@S
def e():
    L('seltype before replace', eng.selection_type())
    L('replace', eng.paste_data('text/rtf', omml.to_rtf("a^2+b^2=c^2")))
@S
def f():
    eng.save_as('/tmp/p6.docx','docx',keep=False)
    import zipfile; x=zipfile.ZipFile('/tmp/p6.docx').read('word/document.xml').decode()
    L('count omath', x.count('<m:oMath'), 'quad left', 'm:rad' in x)
    import re; L(re.sub('<[^>]+>','',x)[:200])
    Gtk.main_quit()
def run(i=0):
    steps[i]()
    if i+1<len(steps): GLib.timeout_add(1200, run, i+1)
    return False
eng.connect('loaded', lambda e,ok: GLib.timeout_add(1500, run))
eng.open(sys.argv[1]); win.show_all(); Gtk.main()
