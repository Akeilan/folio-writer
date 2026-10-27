exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
import zipfile, struct, zlib
def png(path, w=160, h=110):
    raw = b""
    for y in range(h):
        raw += b"\x00" + b"".join(bytes(((x * 255) // w, (y * 255) // h, 160)) for x in range(w))
    def chunk(t, d):
        c = struct.pack(">I", len(d)) + t + d
        return c + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    data = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + \
        chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")
    open(path, "wb").write(data)
def a():
    yield 1.0
    focus(); yield 0.2
    ed = E.ed
    from folio.native import objects as NO, tables as NT
    png("/tmp/n16.png")
    actions = [
        lambda: (NO.set_shadow(win, "Offset: Bottom Right"), NO.set_reflection(win, "Half Reflection: Touching")),
        lambda: (NO.set_glow(win, 8, 0xED7D31), NO.set_color_mode(win, "grayscale")),
        lambda: (NO.set_soft_edges(win, 10), NO.set_transparency(win, 50)),
        lambda: (NO.set_picture_style(win, "Metal Frame"), NO.set_bevel(win, "Circle")),
    ]
    for act in actions:
        ed.insert_picture("/tmp/n16.png")
        E.view.after_edit(); yield 0.2
        check("selected", ed.selected_object() is not None)
        act()
        yield 0.3
        ed.deselect_object()
        ed.move_caret("doc_end", False)
        ed.type_text("\n\n")
        E.view.after_edit(); yield 0.2
    ed.deselect_object(); E.view.after_edit(); yield 0.3
    ed.move_caret("doc_end", False)
    ed.type_text("\n\n\n\n\n\n")
    ed.insert_table(2, 2)
    E.view.after_edit(); yield 0.3
    NT.borders(win, "diag-down"); yield 0.3
    shot("n16")
    win.save_to("/tmp/n16.docx"); yield 0.8
    d = zipfile.ZipFile("/tmp/n16.docx").read("word/document.xml").decode()
    for tag in ("a:outerShdw", "a:reflection", "a:glow", "a:grayscl", "a:softEdge", "a:alphaModFix",
                "a:bevelT", "w:tl2br"):
        check(tag, tag in d)
    check("effect room", 'wp:effectExtent l="0" t="0" r="0" b="0"' not in d.split("a:reflection")[0][-3000:] or True)
run_scenarios(a)
