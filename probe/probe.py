import sys, json, time
sys.path.insert(0,'/home/claude/folio2/app')
from folio.engine import Engine
from gi.repository import Gtk, GLib
eng=Engine('/tmp/folio2-probe-profile')
win=Gtk.Window(); win.set_default_size(1200,800); sw=Gtk.ScrolledWindow(); sw.add(eng.view); win.add(sw)
out=open('/tmp/probe.log','w')
def L(*a): out.write(' '.join(str(x) for x in a)+'\n'); out.flush()
log_states=[]
eng.connect('state-changed', lambda e,c,v: log_states.append((c,v)))
steps=[]
def step(fn, delay=700): steps.append((fn,delay))
def run_steps():
    if not steps: Gtk.main_quit(); return False
    fn,d=steps.pop(0)
    try: fn()
    except Exception as ex: L('ERR', repr(ex))
    GLib.timeout_add(d, run_steps); return False
def dump(tag, keys):
    L('--', tag, {k: eng.get(k)[:120] for k in keys})
K=['.uno:LeftRightParaMargin','.uno:ULSpacing','.uno:LineSpacing','.uno:ParaLeftMargin','.uno:CaseMap','.uno:SmallCaps','.uno:CharFontName','.uno:FontHeight','.uno:StyleApply','.uno:StateWordCount','.uno:StatePageNumber','.uno:Bold','.uno:Color','.uno:CharBackColor','.uno:Underline','.uno:LeftPara','.uno:CenterPara','.uno:SpacePara1','.uno:SpacePara15','.uno:SpacePara2','.uno:HangingIndent','.uno:Hidden','.uno:ModifiedStatus','.uno:Undo','.uno:Redo','.uno:Paste','.uno:SuperScript','.uno:SubScript','.uno:WordCountDialog','.uno:TrackChanges']
tests = [
 ('.uno:LeftRightParaMargin', {"LRSpace.TextLeftMargin": ("long", 1270)}),
 ('.uno:LeftRightParaMargin', {"LRSpace.LeftMargin": ("long", 2540), "LRSpace.TextLeftMargin": ("long", 2540)}),
 ('.uno:CaseMap', {"CaseMap": ("short", 1)}),
 ('.uno:CharCaseMap', {"CharCaseMap": ("short", 1)}),
 ('.uno:LineSpacing', {"LineSpacing.Mode": ("short", 0), "LineSpacing.Height": ("short", 200)}),
 ('.uno:Hidden', {}),
 ('.uno:SmallCaps', {}),
 ('.uno:Shadowed', {}),
 ('.uno:Strikeout', {}),
 ('.uno:UnderlineDouble', {}),
 ('.uno:Underline', {"Underline.LineStyle": ("short", 1)}),
 ('.uno:CharBackColor', {"CharBackColor.Color": ("long", 0xFFFF00)}),
 ('.uno:BackColor', {"BackColor": ("long", 0x00FF00)}),
]
idx=[0]
def s1():
    eng.view.grab_focus()
    for ch in "Hello world":
        pass
    eng.command('.uno:InsertText', {"Text": "Hello world"} )
def s2():
    eng.command('.uno:SelectAll')
def runtest():
    i=idx[0]
    if i>=len(tests): return
    cmd,args=tests[i]; idx[0]+=1
    before=dict(eng.state)
    eng.command(cmd,args)
    def after():
        changed={k:v[:90] for k,v in eng.state.items() if before.get(k)!=v and k not in ('.uno:StateWordCount',)}
        L('TEST', cmd, args, '->', changed)
        return False
    GLib.timeout_add(600, after)
step(s1,900); step(s2,900)
for _ in range(13): step(runtest, 1000)
def loaded(e, ok):
    L('loaded', ok); GLib.timeout_add(1500, run_steps)
eng.connect('loaded', loaded)
eng.open(sys.argv[1])
win.show_all(); Gtk.main()
L('STATE SAMPLE', [(c,v[:80]) for c,v in log_states if c in ('.uno:LeftRightParaMargin','.uno:ULSpacing','.uno:LineSpacing','.uno:CaseMap')][:20])
