# helpers for test scripts run inside the app (exec'd with win, app, GLib, Gtk)
import subprocess, time, os, traceback
LOG = open("/tmp/ftest.log", "a")
def log(*a):
    LOG.write(" ".join(str(x) for x in a) + "\n"); LOG.flush()
def shot(name):
    subprocess.run(["import", "-window", "root", "/tmp/fshot_%s.png" % name], env=dict(os.environ, DISPLAY=os.environ.get("DISPLAY", ":99")))
def pump(sec=0.5):
    end = time.time() + sec
    while time.time() < end:
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)
        time.sleep(0.02)
def steps(*fns, delay=1200):
    fns = list(fns)
    def nxt():
        if not fns:
            return False
        f = fns.pop(0)
        try:
            f()
        except Exception:
            log("ERROR in", getattr(f, "__name__", f)); log(traceback.format_exc())
        GLib.timeout_add(delay, nxt)
        return False
    GLib.timeout_add(100, nxt)
