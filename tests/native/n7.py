exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
def a():
    yield 1.0
    focus(); yield 0.2
    from gi.repository import GdkPixbuf
    pb = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, 240, 160)
    pb.fill(0x3366ccff)
    pb.savev("/tmp/n7.png", "png", [], [])
    T("Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt "
      "ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco "
      "laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in "
      "voluptate velit esse cillum dolore eu fugiat nulla pariatur. ")
    yield 0.3
    E.ed.move_caret("doc_start", False); yield 0.1
    check("inserted", E.ed.insert_picture("/tmp/n7.png"))
    E.view.after_edit(); yield 0.5
    o = E.ed.selected_object()
    check("selected inline picture", o and o["inline"] and o["kind"] == "picture", o)
    check("Picture Format shown", win.ribbon.contextual_visible("Picture Format")
          if hasattr(win.ribbon, "contextual_visible") else True)
    win.object_call("set_wrap", "square"); yield 0.4
    o2 = E.ed.selected_object()
    check("square wrap", o2 and o2["wrap"] == "square" and not o2["inline"], o2)
    # drag the bottom-right handle out by 60px
    v = E.view
    r = v.objs.rect()
    x1, y1 = r[0] + r[2], r[1] + r[3]
    v.objs.press(x1, y1, False)
    class Ev: pass
    ev = Ev(); ev.x, ev.y, ev.state = x1 + 60, y1 + 40, 0
    v.objs.motion(ev); v.objs.release(); yield 0.4
    o3 = E.ed.selected_object()
    check("resized keeping proportions", o3 and o3["w"] > o2["w"] + 30 and
          abs(o3["w"] / o3["h"] - o2["w"] / o2["h"]) < 0.02, (o2, o3))
    # move it right
    r = v.objs.rect()
    v.objs.press(r[0] + r[2] / 2, r[1] + r[3] / 2, False)
    ev.x, ev.y = r[0] + r[2] / 2 + 120, r[1] + r[3] / 2
    v.objs.motion(ev); v.objs.release(); yield 0.4
    o4 = E.ed.selected_object()
    check("moved", o4 and o4["x"] > o3["x"] + 50, (o3, o4))
    shot("n7")
    E.ed.undo(); E.view.after_edit(); yield 0.3
    check("undo move", abs(E.ed.selected_object()["x"] - o3["x"]) < 1, E.ed.selected_object())
    ok = win.save_to("/tmp/n7.docx"); yield 1.0
    check("saved", ok)
    import zipfile
    z = zipfile.ZipFile("/tmp/n7.docx")
    d = z.read("word/document.xml").decode()
    check("anchor saved", "wp:anchor" in d and "wp:wrapSquare" in d, d[:300])
    check("media saved", any(n.startswith("word/media/") for n in z.namelist()))
    ct = z.read("[Content_Types].xml").decode()
    check("png content type", 'Extension="png"' in ct)
    K("Delete"); yield 0.3
    check("deleted", E.ed.selected_object() is None and "￼" not in E.ed.selected_text())
run_scenarios(a)
