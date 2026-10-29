import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
import zipfile
def a():
    yield 1.0
    focus(); yield 0.2
    ed = E.ed
    v = E.view
    win.dialogs.message = lambda *a, **k: None
    for i in range(8):
        ed.type_text("Body paragraph %d of the document under the shapes.\n" % i)
    v.after_edit(); yield 0.3
    # draw a rectangle by dragging
    win.run(("draw-shape", "rectangle")); yield 0.2
    x0, y0 = v.to_widget(0, 150, 300)
    x1, y1 = v.to_widget(0, 300, 400)
    rx, ry = v.get_window().get_root_origin() if False else (0, 0)
    ox, oy = v.get_window().get_origin()[1:]
    X("mousemove", int(ox + x0), int(oy + y0)); yield 0.1
    X("mousedown", 1); yield 0.1
    X("mousemove", int(ox + (x0 + x1) / 2), int(oy + (y0 + y1) / 2)); yield 0.1
    X("mousemove", int(ox + x1), int(oy + y1)); yield 0.1
    X("mouseup", 1); yield 0.6
    o = ed.selected_object()
    check("rectangle drawn", o is not None and abs(o["w"] - 150) < 3 and abs(o["h"] - 100) < 3, o)
    win.object_call("set_fill", 0xFF0000); yield 0.2
    win.object_call("change_shape", "ellipse"); yield 0.2
    win.object_call("set_shape_style", 2, 0xED7D31); yield 0.3
    # a text box by clicking: then typing goes into it
    win.run(("draw-shape", "textbox")); yield 0.2
    tx, ty = v.to_widget(0, 400, 440)
    ox, oy = v.get_window().get_origin()[1:]
    X("mousemove", int(ox + tx), int(oy + ty)); yield 0.1
    X("mousedown", 1); yield 0.05
    X("mouseup", 1); yield 0.6
    check("editing text box", ed.story() == "textbox", ed.story())
    T("Hello box"); yield 0.4
    win.object_call_module("textlinks", "set_align", "CENTER"); yield 0.2
    K("Escape"); yield 0.3
    check("esc selects box", ed.story() == "body" and ed.selected_object() is not None)
    # built-in text box
    K("Escape"); yield 0.2
    ed.move_caret("doc_start", False); v.after_move()
    win.model_call_sync("insertextras.insert_textbox", "sidebar"); yield 0.5
    shot("n21")
    win.save_to("/tmp/n21.docx"); yield 0.6
    d = zipfile.ZipFile("/tmp/n21.docx").read("word/document.xml").decode()
    check("ellipse saved", 'prst="ellipse"' in d)
    check("text box saved", "Hello box" in d and "w:txbxContent" in d and 'anchor="ctr"' in d)
    check("sidebar saved", "[Sidebar Title]" in d and "D9E2F3" in d)
    # reopen: a click in the text box edits it
    ed.edit_header_footer(None)
    ok = False
    for pg in range(ed.page_count()):
        pass
    check("still one page", ed.page_count() == 1, ed.page_count())
run_scenarios(a)
