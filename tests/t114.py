exec(open("/home/claude/folio2/tests/common.py").read())
from folio import docapi
from gi.repository import Gdk
A = win.actions
adj = win.canvas.get_vadjustment()
def s0():
    for i in range(60):
        A.insert_text("Paragraph %d with some text. " % i * 4)
        win.engine.command(".uno:InsertPara")
    win.engine.view.grab_focus()
def chk(n): return lambda: log(n, adj.get_value(), docapi.read_cursor(win.engine.model).getPosition().Y)
def run(*a): return lambda: subprocess.Popen(["xdotool"] + list(a))
steps(s0, chk("a"), lambda: win.engine.post_key(1028|8192), chk("top"), run("key","ctrl+Home"), chk("ctrl+Home"), run("key","ctrl+End"), chk("ctrl+End"), run("key","ctrl+shift+Home"), chk("ctrl+shift+Home"), run("key","Right"), chk("Right"), run("key","ctrl+End"), chk("ctrl+End"), run("key","ctrl+Prior"), chk("ctrl+Prior"), run("key","ctrl+Next"), chk("ctrl+Next"), run("key","ctrl+Left"), chk("ctrl+Left"), run("key","shift+Prior"), chk("shift+Prior"), run("key","shift+End"), chk("shift+End"), run("key","shift+Home"), chk("shift+Home"), run("key","End"), chk("End"), run("key","Home"), chk("Home"), lambda: app.quit(), delay=700)
