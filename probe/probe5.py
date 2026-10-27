import sys
sys.path.insert(0,'/home/claude/folio2/app')
from folio.engine import Engine
from gi.repository import Gtk, GLib
eng=Engine('/tmp/folio2-probe-profile')
win=Gtk.Window(); win.set_default_size(900,700); sw=Gtk.ScrolledWindow(); sw.add(eng.view); win.add(sw)
out=open('/tmp/probe5.log','w')
def L(*a): out.write(' '.join(str(x) for x in a)+'\n'); out.flush()
steps=[]
def S(f): steps.append(f); return f
@S
def a():
    eng.command('.uno:InsertText', {"Text":"before "})
    L('html', eng.paste_data('text/html', '<html><body><a href="https://example.com/">Link text</a></body></html>'))
@S
def b():
    L('plain', eng.paste_data('text/plain;charset=utf-8', ' plainpaste '))
@S
def c0():
    r=r"{\rtf1\ansi{\fonttbl{\f0 Cambria Math;}}{\mmathPr{\mmathFont0}}\pard{\mmath {\*\moMath {\mr x}{\mr =}{\mf {\mnum {\mr a}}{\mden {\mr 2}}}}}\par}"
    L('rtf', eng.paste_data('text/rtf', r))
@S
def c():
    d=open('/tmp/snip/eq.odt','rb').read()
    L('odt', eng.paste_data('application/x-openoffice-embed-source-xml;windows_formatname="Star Embed Source (XML)"', d))
@S
def d():
    d=open('/tmp/snip/eq.odt','rb').read()
    L('odt2', eng.paste_data('application/vnd.oasis.opendocument.text', d))
@S
def e():
    eng.command('.uno:SelectAll')
@S
def f():
    L('text', repr(eng.selection()[:300]))
    h=eng.selection('text/html')
    L('href' , 'example.com' in h, 'img/obj', h.count('<img'), h.count('<object'))
    eng.save_as('/tmp/p5.docx','docx',keep=False)
    import zipfile; x=zipfile.ZipFile('/tmp/p5.docx').read('word/document.xml').decode()
    L('docx link', 'hyperlink' in x, 'omath', 'oMath' in x, 'plainpaste' in x)
    Gtk.main_quit()
def run(i=0):
    steps[i]()
    if i+1<len(steps): GLib.timeout_add(1200, run, i+1)
    return False
eng.connect('loaded', lambda e,ok: GLib.timeout_add(1500, run))
eng.open(sys.argv[1]); win.show_all(); Gtk.main()
