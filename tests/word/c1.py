exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
H = "/home/claude/folio2/tests/word/helpers/"
procs = []
ENV = dict(os.environ, DISPLAY=os.environ.get("DISPLAY", ":99"))
def spawn(*args):
    p = subprocess.Popen(list(args), env=ENV, stdin=subprocess.PIPE if args[0] == "xclip" else None)
    procs.append(p); return p
def xclip_set(data, mime="UTF8_STRING"):
    p = subprocess.Popen(["xclip", "-selection", "clipboard", "-t", mime, "-i"], env=ENV, stdin=subprocess.PIPE)
    p.stdin.write(data.encode()); p.stdin.close(); procs.append(p)
def xclip_get(target="UTF8_STRING"):
    # without blocking our own main loop: run, then pump until done
    p = subprocess.Popen(["xclip", "-selection", "clipboard", "-o", "-t", target], env=ENV, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    return p
def kill():
    for p in procs:
        try: p.kill()
        except Exception: pass
    del procs[:]
def a_external_first():
    fresh(); yield 0.3
    xclip_set("External clipboard text"); yield 0.8
    focus(); K("ctrl+v"); yield 1.2
    check("paste text copied in another app", "External clipboard text" in text(), repr(text()))
    kill()
def b_after_own_copy():
    fresh(); yield 0.3
    T("internal words"); K("ctrl+a"); K("ctrl+b"); K("ctrl+c"); yield 0.8
    K("End"); yield 0.2
    xclip_set("Newer outside copy"); yield 0.8
    focus(); K("ctrl+v"); yield 1.2
    check("after copying in Folio, paste takes a newer outside copy", "Newer outside copy" in text(), repr(text()))
    kill()
def b2_own_copy_still_works():
    fresh(); yield 0.3
    T("bold words"); K("ctrl+a"); K("ctrl+b"); K("ctrl+c"); yield 0.8
    K("End"); K("Return"); K("ctrl+v"); yield 1.2
    f = find("bold", 1)
    check("own copy pastes with formatting", f is not None and f.CharWeight > 100, f and f.CharWeight)
def c_html():
    fresh(); yield 0.3
    xclip_set("<p><i>External</i> rich clipboard</p>", "text/html"); yield 0.8
    focus(); K("ctrl+v"); yield 1.5
    f = find("External")
    check("paste rich text from another app keeps formatting", f is not None and f.CharPosture.value == "ITALIC", (repr(text()), f and f.CharPosture.value))
    kill()
def d_drag_in():
    fresh(); yield 0.3
    T("Drop here: "); yield 0.4
    spawn("/usr/bin/python3", H + "ext_src.py", "none"); yield 2.0
    x0, y0, w, h = win._follow_rect
    dx, dy = doc_screen(x0 + 200, y0 + h / 2)
    sx, sy = 1320 + 100, 120 + 50
    X("mousemove", sx, sy); yield 0.3; X("mousedown", 1); yield 0.3
    for i in range(1, 30):
        X("mousemove", int(sx + (dx - sx) * i / 29), int(sy + (dy - sy) * i / 29)); yield 0.05
    yield 0.5; X("mouseup", 1); yield 2.0
    check("drag text in from another app", "Dragged" in text(), repr(text()))
    shot("c1_drag")
    kill()
def e_copy_out():
    fresh(); yield 0.3
    T("Copy me out"); K("ctrl+a"); K("ctrl+c"); yield 1.0
    p = xclip_get()
    for i in range(50):
        if p.poll() is not None: break
        yield 0.1
    out = p.stdout.read().decode() if p.poll() is not None else "<timeout>"
    check("text copied in Folio pastes in another app", out.strip() == "Copy me out", repr(out))
    p = xclip_get("text/html")
    for i in range(50):
        if p.poll() is not None: break
        yield 0.1
    out = p.stdout.read().decode() if p.poll() is not None else "<timeout>"
    check("other apps get formatted text (HTML) too", "Copy me out" in out and "<" in out, out[:80])
def f_drag_out():
    fresh(); yield 0.3
    T("Take me away"); yield 0.3
    try: os.remove("/tmp/c1_drop.txt")
    except Exception: pass
    spawn("/usr/bin/python3", H + "ext_dst.py", "/tmp/c1_drop.txt"); yield 2.0
    docapi.controller(M()).select(find("Take me")); yield 0.6
    c = vc(); r = find("Take me"); c.gotoRange(r.getStart(), False); yield 0.3
    x0, y0, w, h = win._follow_rect
    docapi.controller(M()).select(find("Take me")); yield 0.6
    sx, sy = doc_screen(x0 + 300, y0 + h / 2)
    dx, dy = 1320 + 130, 400 + 100
    X("mousemove", sx, sy); yield 0.3; X("mousedown", 1); yield 0.3
    for i in range(1, 40):
        X("mousemove", int(sx + (dx - sx) * i / 39), int(sy + (dy - sy) * i / 39)); yield 0.05
    yield 0.5; X("mouseup", 1); yield 2.0
    got = open("/tmp/c1_drop.txt").read() if os.path.exists("/tmp/c1_drop.txt") else None
    check("drag text out to another app", got == "Take me", repr(got))
    check("dragging out leaves the document alone", "Take me away" in text(), repr(text()))
    kill()
def g_middle():
    fresh(); yield 0.3
    p = subprocess.Popen(["xclip", "-selection", "primary", "-i"], env=ENV, stdin=subprocess.PIPE)
    p.stdin.write(b"primary words"); p.stdin.close(); procs.append(p); yield 0.6
    x0, y0, w, h = win._follow_rect
    sx, sy = doc_screen(x0 + 10, y0 + h / 2)
    X("mousemove", sx, sy); X("click", 2); yield 1.2
    check("middle-click pastes the desktop selection", "primary words" in text(), repr(text()))
    kill()
run_scenarios(a_external_first, b_after_own_copy, b2_own_copy_still_works, c_html, d_drag_in, e_copy_out, f_drag_out, g_middle)
