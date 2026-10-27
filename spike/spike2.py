import sys, os, json, ctypes, time
import gi
gi.require_version('Gtk','3.0'); gi.require_version('LOKDocView','0.1')
from gi.repository import Gtk, LOKDocView, GLib
LO='/usr/lib/libreoffice/program'
view=LOKDocView.View.new_from_user_profile(LO, 'file:///tmp/folio2-spike-profile', None)
win=Gtk.Window(); win.set_default_size(1200,800); sw=Gtk.ScrolledWindow(); sw.add(view); win.add(sw)
log=open('/tmp/spike2.log','w')
def L(*a): log.write(' '.join(str(x) for x in a)+'\n'); log.flush()
state={}
view.connect('command-changed', lambda v,s: state.__setitem__(s.split('=')[0], s.split('=',1)[-1]) if s.startswith('.uno') else None)
view.connect('command-result', lambda v,s: L('RESULT', s[:200]))

class DocClass(ctypes.Structure):
    _fields_=[('nSize',ctypes.c_size_t),('destroy',ctypes.c_void_p),
              ('saveAs',ctypes.CFUNCTYPE(ctypes.c_int,ctypes.c_void_p,ctypes.c_char_p,ctypes.c_char_p,ctypes.c_char_p))]
class Doc(ctypes.Structure):
    _fields_=[('pClass',ctypes.POINTER(DocClass))]

def steps():
    L('fonts', (view.get_command_values('.uno:CharFontName') or '')[:150])
    L('styles', (view.get_command_values('.uno:StyleApply') or '')[:300])
    view.post_command('.uno:SelectAll','{}',False)
    view.post_command('.uno:Bold','{}',False)
    GLib.timeout_add(800, steps2)
    return False
def steps2():
    L('Bold state', state.get('.uno:Bold'))
    args=json.dumps({"FontHeight.Height":{"type":"float","value":"16"}})
    view.post_command('.uno:FontHeight', args, False)
    view.post_command('vnd.sun.star.script:probe.py$run?language=Python&location=user','{}',False)
    GLib.timeout_add(1500, steps3); return False
def steps3():
    L('FontHeight', state.get('.uno:FontHeight'), 'probe file exists', os.path.exists('/tmp/probe_ran'))
    ptr=view.get_property('docpointer')
    L('docpointer', ptr)
    try:
        d=ctypes.cast(ctypes.c_void_p(int(ptr) if not isinstance(ptr,int) else ptr), ctypes.POINTER(Doc))
        r=d.contents.pClass.contents.saveAs(d, b'file:///tmp/spike_out.docx', b'docx', None)
        L('saveAs ->', r, os.path.exists('/tmp/spike_out.docx'))
    except Exception as e:
        L('saveAs error', repr(e))
    GLib.timeout_add(500, Gtk.main_quit); return False
def loaded(src,res,data=None):
    L('loaded', view.open_document_finish(res)); view.set_edit(True)
    GLib.timeout_add(1500, steps)
view.open_document(sys.argv[1], '{}', None, loaded, None)
win.show_all(); Gtk.main()
