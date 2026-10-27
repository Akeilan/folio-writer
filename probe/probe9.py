import sys, time
sys.path.insert(0,'/home/claude/folio2/app')
from folio import bridge
bridge.prepare_path(); bridge.install('/tmp/folio2-probe-profile')
from folio import engine as E
from gi.repository import Gtk, GLib
eng=E.Engine('/tmp/folio2-probe-profile')
eng.model=None
eng._set_model=lambda m: setattr(eng,'model',m)
win=Gtk.Window(); win.set_default_size(900,700); sw=Gtk.ScrolledWindow(); sw.add(eng.view); win.add(sw)
out=open('/tmp/probe9.log','w')
def L(*a): out.write(' '.join(str(x) for x in a)+'\n'); out.flush()
def go():
    bridge.request(eng); GLib.timeout_add(1500, use); return False
def use():
    m=eng.model; L('model', m is not None)
    t=time.time()
    L('text', repr(m.getText().getString()[:60]))
    vc=m.getCurrentController().getViewCursor(); L('page style', vc.PageStyleName, 'para', vc.ParaStyleName)
    st=m.getStyleFamilies().getByName("PageStyles").getByName(vc.PageStyleName)
    st.FillStyle=bridge.enum("com.sun.star.drawing.FillStyle","SOLID"); st.FillColor=0xDDEEFF
    L('stats', [(p.Name,p.Value) for p in m.getDocumentProperties().DocumentStatistics])
    # bookmark
    bm=m.createInstance("com.sun.star.text.Bookmark"); bm.setName("Mark1")
    m.getText().insertTextContent(vc, bm, False)
    L('bookmarks', m.getBookmarks().getElementNames())
    L('elapsed', round(time.time()-t,3))
    GLib.timeout_add(1500, fin); return False
def fin():
    import zipfile,re
    eng.save_as('/tmp/p9.docx','docx',keep=False); x=''.join(zipfile.ZipFile('/tmp/p9.docx').read(n).decode(errors='ignore') for n in ['word/document.xml'])
    L('docx bg', re.findall('w:background[^>]*',x), 'Mark1' in x); Gtk.main_quit(); return False
eng.connect('loaded', lambda e,ok: GLib.timeout_add(1200, go))
eng.open(sys.argv[1]); win.show_all(); Gtk.main()
