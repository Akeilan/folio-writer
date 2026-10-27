import sys, os, zipfile, re
sys.path.insert(0,'/home/claude/folio2/app')
from folio.engine import Engine
from gi.repository import Gtk, GLib
eng=Engine('/tmp/folio2-probe-profile')
win=Gtk.Window(); win.set_default_size(900,700); sw=Gtk.ScrolledWindow(); sw.add(eng.view); win.add(sw)
out=open('/tmp/probe2.log','w')
def L(*a): out.write(' '.join(str(x) for x in a)+'\n'); out.flush()
CASES=[
 ('caps', '.uno:CaseMap', {"CaseMap": ("short",1)}, r'<w:caps/>|<w:caps w:val="(true|1)"'),
 ('caps2', '.uno:ChangeCaseToUpper', {}, None),
 ('smallcaps', '.uno:SmallCaps', {}, r'<w:smallCaps'),
 ('hidden', '.uno:Hidden', {}, r'<w:vanish'),
 ('linesp', '.uno:LineSpacing', {"LineSpacing.Mode": ("short",0), "LineSpacing.Height": ("short",200)}, r'w:line="480"'),
 ('linesp2', '.uno:SpacePara2', {}, r'w:line="480"'),
 ('hang', '.uno:HangingIndent', {}, r'w:hanging'),
 ('dblstrike', '.uno:Strikeout', {"Strikeout.Kind": ("short",2)}, r'<w:dstrike'),
 ('superscript', '.uno:SuperScript', {}, r'superscript'),
 ('highlight', '.uno:CharBackColor', {"CharBackColor.Color": ("long", 0xFFFF00)}, r'<w:highlight|<w:shd'),
 ('wordunderline', '.uno:Underline', {"Underline.LineStyle": ("short",1)}, r'<w:u '),
 ('wordsonly', '.uno:WordUnderline', {}, r'w:val="words"'),
 ('undl_words', '.uno:CharUnderline', {"CharUnderline": ("short",1)}, None),
]
i=[0]
def nextcase():
    if i[0]>=len(CASES): Gtk.main_quit(); return False
    name,cmd,args,pat=CASES[i[0]]; i[0]+=1
    eng.command('.uno:SelectAll'); eng.command('.uno:Delete')
    eng.command('.uno:InsertText', {"Text":"Sample text here"})
    eng.command('.uno:SelectAll')
    eng.command(cmd,args)
    def save():
        p='/tmp/pr_%s.docx'%name
        ok=eng.save_as(p,'docx',keep=False)
        xml=zipfile.ZipFile(p).read('word/document.xml').decode() if ok else ''
        body=xml[xml.find('<w:body>'):][:700]
        hit = bool(re.search(pat, xml)) if pat else None
        L(name, cmd, 'saved', ok, 'match', hit, '|', re.sub(r'<w:sectPr.*','',body)[:400])
        GLib.timeout_add(300, nextcase); return False
    GLib.timeout_add(900, save); return False
def loaded(e,ok): L('loaded',ok); GLib.timeout_add(1200, nextcase)
eng.connect('loaded', loaded); eng.open(sys.argv[1]); win.show_all(); Gtk.main()
