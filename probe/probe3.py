import sys, os, zipfile, re
sys.path.insert(0,'/home/claude/folio2/app')
from folio.engine import Engine, file_url
from gi.repository import Gtk, GLib, GObject, LOKDocView
eng=Engine('/tmp/folio2-probe-profile')
win=Gtk.Window(); win.set_default_size(900,700); sw=Gtk.ScrolledWindow(); sw.add(eng.view); win.add(sw)
out=open('/tmp/probe3.log','w')
def L(*a): out.write(' '.join(str(x) for x in a)+'\n'); out.flush()
L('signals', [GObject.signal_name(i) for i in GObject.signal_list_ids(LOKDocView.View)])
L('tiled-annotations', eng.view.get_property('tiled-annotations'))
def doc_xml(name):
    p='/tmp/pr3_%s.docx'%name
    eng.save_as(p,'docx',keep=False)
    z=zipfile.ZipFile(p)
    return z.read('word/document.xml').decode(), z.namelist()
CASES=[
 ('lrmargin', '.uno:PageLRMargin', {"PageLRMargin.Left":("long",1270),"PageLRMargin.Right":("long",1270)}, r'w:left="720"'),
 ('ulmargin', '.uno:PageULMargin', {"PageULMargin.Upper":("long",1270),"PageULMargin.Lower":("long",1270)}, r'w:top="720"'),
 ('orient', '.uno:Orientation', {"Orientation":("boolean","true")}, r'w:orient="landscape"'),
 ('papersize', '.uno:AttributePageSize', {"AttributePageSize.Width":("long",21590),"AttributePageSize.Height":("long",35560)}, r'w:h="20160"'),
 ('columns', '.uno:PageColumnType', {"PageColumnType":("short",2)}, r'<w:cols w:num="2"'),
 ('watermark', '.uno:Watermark', {"Text":("string","DRAFT"),"Font":("string","Carlito"),"Angle":("short",45),"Transparency":("short",50),"Color":("long",0xC0C0C0)}, r'DRAFT'),
 ('pagecolor', '.uno:FillPageColor', {"Color":("long",0xDDEEFF)}, r'w:background|DDEEFF'),
 ('header', '.uno:InsertPageHeader', {"PageStyle":("string","Standard"),"On":("boolean","true")}, r'headerReference'),
 ('picture', '.uno:InsertGraphic', {"FileName":("string",file_url('/tmp/snip/pic.png'))}, r'<w:drawing|<pic:pic'),
 ('hyperlink', '.uno:SetHyperlink', {"Hyperlink.Text":("string","Folio"),"Hyperlink.URL":("string","https://example.org/"),"Hyperlink.Type":("short",1)}, r'example\.org'),
 ('bookmark', '.uno:InsertBookmark', {"Bookmark":("string","MyMark")}, r'MyMark'),
 ('comment', '.uno:InsertAnnotation', {"Text":("string","A note")}, r'commentReference|A note'),
 ('insertdoc', '.uno:InsertDoc', {"Name":("string",file_url('/tmp/snip/eq.odt')),"Filter":("string","writer8")}, r'<m:oMath'),
 ('table', '.uno:InsertTable', {"Columns":("short",3),"Rows":("short",2)}, r'<w:tbl>'),
]
i=[0]
def nextcase():
    if i[0]>=len(CASES): Gtk.main_quit(); return False
    name,cmd,args,pat=CASES[i[0]]; i[0]+=1
    eng.command('.uno:GoToEndOfDoc')
    eng.command('.uno:InsertText', {"Text":" probe "})
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
def loaded(e,ok): L('loaded',ok); GLib.timeout_add(1200, nextcase)
eng.connect('loaded', loaded); eng.open(sys.argv[1]); win.show_all(); Gtk.main()
