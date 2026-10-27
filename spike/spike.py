import sys, os
import gi
gi.require_version('Gtk','3.0'); gi.require_version('LOKDocView','0.1')
from gi.repository import Gtk, LOKDocView, GLib
LO='/usr/lib/libreoffice/program'
profile='file:///tmp/folio2-spike-profile'
win=Gtk.Window(title='Spike'); win.set_default_size(1400,900)
box=Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
lab=Gtk.Label(label='OWN UI BAR'); box.pack_start(lab,False,False,6)
view=LOKDocView.View.new_from_user_profile(LO, profile, None)
sw=Gtk.ScrolledWindow(); sw.add(view); box.pack_start(sw,True,True,0)
win.add(box)
log=open('/tmp/spike.log','w')
def on_loaded(src,res,data=None):
    ok=view.open_document_finish(res)
    log.write('loaded %s parts=%s\n'%(ok, view.get_parts())); log.flush()
    view.set_edit(True)
def on_cmd(v, s): log.write('cmd %s\n'%s); log.flush()
view.connect('command-result', on_cmd)
view.connect('command-changed', lambda v,s: (log.write('state %s\n'%s), log.flush()))
view.open_document(sys.argv[1], '{}', None, on_loaded, None)
win.connect('destroy', Gtk.main_quit); win.show_all(); Gtk.main()
