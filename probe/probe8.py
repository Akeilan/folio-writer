import sys, zipfile, re, json, os, ctypes
sys_path_fix=__import__('sys').path.append('/usr/lib/libreoffice/program')
sys.path.insert(0,'/home/claude/folio2/app')
from folio import engine as E
from gi.repository import Gtk, GLib
eng=E.Engine('/tmp/folio2-probe-profile')
win=Gtk.Window(); win.set_default_size(900,700); sw=Gtk.ScrolledWindow(); sw.add(eng.view); win.add(sw)
out=open('/tmp/probe8.log','w')
def L(*a): out.write(' '.join(str(x) for x in a)+'\n'); out.flush()
URL="vnd.sun.star.script:folio_bridge.py$run?language=Python&location=user"
def go():
    json.dump({"op":"page_color","color":0xDDEEFF}, open('/tmp/folio_bridge.req','w'))
    eng.view.post_command(URL, "{}", True)
    GLib.timeout_add(2000, check, 'view')
    return False
def go2():
    os.path.exists('/tmp/folio_bridge.res') and os.remove('/tmp/folio_bridge.res')
    doc=eng._doc_ptr()
    fn=ctypes.cast(ctypes.cast(doc.contents.pClass, ctypes.POINTER(ctypes.c_void_p))[17], ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_bool))
    fn(doc, URL.encode(), b"{}", False)
    GLib.timeout_add(2000, check, 'ctypes')
    return False
def check(how):
    L(how, 'res', open('/tmp/folio_bridge.res').read() if os.path.exists('/tmp/folio_bridge.res') else None)
    if how=='view': GLib.timeout_add(100, go2)
    else:
        eng.save_as('/tmp/p8.odt','odt',keep=False); s=zipfile.ZipFile('/tmp/p8.odt').read('styles.xml').decode()
        L('fill', re.findall('fill-color="[^"]+"', s)[:3]); Gtk.main_quit()
    return False
eng.view.connect('command-result', lambda v,r: L('cmdres', r))
eng.connect('loaded', lambda e,ok: GLib.timeout_add(1200, go))
eng.open(sys.argv[1]); win.show_all(); Gtk.main()
