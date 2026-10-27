import sys, os, zipfile, re
sys.path.insert(0,'/home/claude/folio2/app')
from folio.engine import Engine, file_url
from gi.repository import Gtk, GLib, GObject, LOKDocView
eng=Engine('/tmp/folio2-probe-profile')
win=Gtk.Window(); win.set_default_size(900,700); sw=Gtk.ScrolledWindow(); sw.add(eng.view); win.add(sw)
out=open('/tmp/probe3.log','w')
def L(*a): out.write(' '.join(str(x) for x in a)+'\n'); out.flush()
L('orientation state', eng.get('.uno:Orientation')) if False else None
#L('signals', [GObject.signal_name(i) for i in GObject.signal_list_ids(LOKDocView.View)])
L('tiled-annotations', eng.view.get_property('tiled-annotations'))
def doc_xml(name):
    p='/tmp/pr3_%s.docx'%name
    eng.save_as(p,'docx',keep=False)
    z=zipfile.ZipFile(p)
    return z.read('word/document.xml').decode(), z.namelist()
CASES=[
 ('seltype', 'SELTYPE', None, r'zzz'),
 ('table_long', '.uno:InsertTable', {"Columns":("long",3),"Rows":("long",2)}, r'<w:tbl>'),
 ('orient_short', '.uno:Orientation', {"Orientation":("short",1)}, r'w:orient="landscape"'),
 ('orient_long', '.uno:Orientation', {"Orientation":("long",1)}, r'w:orient="landscape"'),
 ('orient_paper', '.uno:AttributePage', {"AttributePage.Landscape":("boolean","true")}, r'w:orient="landscape"'),
 ('pagecolor2', '.uno:FillPageColor', {"FillPageColor":("long",0xDDEEFF)}, r'w:background|DDEEFF'),
 ('pagecolor3', '.uno:PageColor', {"Color":("long",0xDDEEFF)}, r'w:background|DDEEFF'),
 ('bookmark2', '.uno:InsertBookmark', {"Name":("string","MyMark")}, r'MyMark'),
 ('hyperlink2', '.uno:SetHyperlink', {"Hyperlink.Text":("string","Folio"),"Hyperlink.URL":("string","https://example.org/"),"Hyperlink.Target":("string",""),"Hyperlink.Name":("string",""),"Hyperlink.Type":("long",1)}, r'example\.org'),
 ('pastehtml', 'PASTE_HTML', None, r'example\.com'),
 ('pasteodt', 'PASTE_ODT', None, r'<m:oMath'),
]
i=[0]
def nextcase():
    if i[0]>=len(CASES): Gtk.main_quit(); return False
    name,cmd,args,pat=CASES[i[0]]; i[0]+=1
    eng.command('.uno:GoToEndOfDoc')
    eng.command('.uno:InsertText', {"Text":" probe "})
    if cmd=='PASTE_HTML':
        d=b'<html><body><a href="https://example.com/">Link text</a></body></html>'
        L('paste html', eng.paste_data('text/html', d))
    elif cmd=='SELTYPE':
        eng.command('.uno:SelectAll'); L('selection text', repr(eng.selection()[:40]), 'type', eng.selection_type())
    elif cmd=='PASTE_ODT':
        d=open('/tmp/snip/eq.odt','rb').read()
        r=eng.paste_data('application/x-openoffice-embed-source-xml;windows_formatname="Star Embed Source (XML)"', d)
        L('paste odt returned', r)
    else:
        eng.command(cmd,args)
    def check():
        try:
            xml,names=doc_xml(name)
            allx=xml
            z=zipfile.ZipFile('/tmp/pr3_%s.docx'%name)
            for n in names:
                if n.endswith('.xml') and n!='word/document.xml' and ('header' in n or 'comments' in n or 'settings' in n):
                    allx+=z.read(n).decode(errors='ignore')
            L(name, cmd, 'match', bool(re.search(pat, allx)))
        except Exception as e:
            L(name, 'ERR', repr(e))
        GLib.timeout_add(200, nextcase); return False
    GLib.timeout_add(1300, check); return False
def loaded(e,ok): L('loaded',ok, 'orient state', eng.get('.uno:Orientation')); GLib.timeout_add(1200, nextcase)
eng.connect('loaded', loaded); eng.open(sys.argv[1]); win.show_all(); Gtk.main()
