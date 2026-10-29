import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
from folio import objlayout as OL
from folio.native import objects as NO, arrange as NA
def pic_node():
    p = objects("Picture")
    return p[0][0] if p else None
def lay():
    E.ed.select_object_node(pic_node())
    return dict(E.ed.object_layout() or [])
def pic():
    fresh(); yield 0.3
    set_text("Text around the picture. " * 30); yield 0.5
    K("ctrl+Home"); yield 0.3
    NO.insert_picture_path(win, "/tmp/dc/pic.png"); yield 0.8
    E.ed.select_object_node(pic_node()); NO.set_wrap(win, "square"); yield 0.5
def layout():
    yield from pic()
    E.ed.select_object_node(pic_node()); E.view.after_move(); yield 0.6
    check("picture selected", E.ed.selected_object() is not None)
    GLib.idle_add(lambda: (win.dialogs.object_size(), False)[1]); yield 1.3
    d = dlg("Layout")
    check("Layout dialog", bool(d))
    nb = find_widget(d[0], lambda w: isinstance(w, Gtk.Notebook))[0]
    tabs = [nb.get_tab_label(nb.get_nth_page(i)).get_text() for i in range(nb.get_n_pages())]
    check("Layout tabs", tabs == ["Position", "Text Wrapping", "Size"], tabs)
    shot("l8_size")
    nb.set_current_page(0); yield 0.4; shot("l8_pos")
    radios = {w.get_label(): w for w in find_widget(d[0], lambda w: isinstance(w, Gtk.RadioButton))}
    radios["Tight"].set_active(True)
    chk = {w.get_label(): w for w in find_widget(d[0], lambda w: isinstance(w, Gtk.CheckButton))}
    chk["_Move object with text"].set_active(False)
    radios["_Alignment"].set_active(True)
    cbs = find_widget(d[0], lambda w: isinstance(w, Gtk.ComboBoxText))
    hal = [c for c in cbs if [r[0] for r in c.get_model()] == ["Left", "Centered", "Right"]]
    hal[0].set_active(1)  # horizontal alignment: centered
    note("before OK", (d[0]._widgets["h_al_rb"].get_active(), d[0]._widgets["h_al"].get_active(), [k for k in radios]))
    respond("Layout"); yield 1.0
    L = lay()
    note("layout", L)
    check("tight wrap", L.get("wrap") == "tight", L.get("wrap"))
    check("fixed on page", L.get("v_rel") in ("page", "margin"), L.get("v_rel"))
    check("centered", L.get("h_align") == "center", L)
    shot("l8_after")
def wrappts():
    E.ed.select_object_node(pic_node()); E.view.after_move(); yield 0.4
    GLib.idle_add(lambda: (OL.edit_wrap_points(win), False)[1]); yield 1.5
    d = dlg("Edit Wrap Points")
    check("Edit Wrap Points dialog", bool(d))
    shot("l8_wrap")
    if d:
        pts = d[0]._points
        note("points", len(pts))
        pts[1][1] = 80
        respond("Edit Wrap Points"); yield 0.8
    E.ed.select_object_node(pic_node())
    poly = E.ed.wrap_polygon()
    note("contour", poly[:4])
    check("contour saved", 2 < len(poly) <= 25 and lay().get("wrap") in ("tight", "through"), (len(poly), lay().get("wrap")))
def crop():
    E.ed.select_object_node(pic_node()); E.view.after_move(); yield 0.3
    o = E.ed.selected_object()
    E.ed.object_resize(o["w"], o["w"]); E.view.after_edit(); yield 0.4   # square frame
    NA.aspect_fill(win); yield 0.4
    c = E.ed.object_crop()
    check("Fill crops sides", c and c[0] > 0 and c[2] > 0, c)
    NA.aspect_fit(win); yield 0.4
    o = E.ed.selected_object(); c = E.ed.object_crop() or (0, 0, 0, 0)
    # as in the original: the frame stays, the whole picture shows inside it (negative crop)
    check("Fit shows the whole picture in the frame", c[0] == 0 and c[2] == 0 and c[1] < 0 and c[3] < 0 and abs(o["w"] - o["h"]) < 0.5, (c, o["w"], o["h"]))
    NA.crop_to_shape(win, "ellipse"); yield 1.0
    x = E.ed.selected_drawing_xml() or ""
    check("crop to shape gives the picture that shape", 'prst="ellipse"' in x and len(objects("Picture")) == 1, objects())
    shot("l8_shape")
    E.ed.select_object_node(objects()[0][0])
    NO.set_glow(win, 8, 0x4472C4); NO.set_soft_edges(win, 5); yield 0.5
    x = E.ed.selected_drawing_xml() or ""
    check("glow / soft edges on shape", "a:glow" in x and "a:softEdge" in x, x[:200])
    shot("l8_glow")
run_scenarios(layout, wrappts, crop)
