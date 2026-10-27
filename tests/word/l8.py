exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
from folio import objlayout as OL, drawing as DR
def pic():
    fresh(); yield 0.3
    M().getText().setString("Text around the picture. " * 30); yield 0.5
    K("ctrl+Home"); yield 0.3
    o = docapi.insert_picture(M(), "/tmp/dc/pic.png"); yield 0.8
    DR.set_wrap(o, "square"); yield 0.3
    docapi.controller(M()).select(o); yield 0.5
    return_obj[0] = o
return_obj = [None]
def layout():
    yield from pic()
    o = return_obj[0]
    docapi.controller(M()).select(o); yield 0.6
    note("sel", DR.selected_shape(M()) is not None)
    def go():
        try: win.dialogs.object_size()
        except Exception as e:
            import traceback; traceback.print_exc()
    GLib.idle_add(lambda: (go(), False)[1]); yield 0.1
    yield 1.2
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
    cbs[0].set_active(1)  # centered
    respond("Layout"); yield 1.0
    check("tight wrap", OL.wrap_of(o) == "tight", OL.wrap_of(o))
    check("fixed on page", o.AnchorType.value == "AT_PAGE", o.AnchorType.value)
    check("centered", o.HoriOrient == 2, o.HoriOrient)
    shot("l8_after")
def wrappts():
    o = return_obj[0]
    docapi.controller(M()).select(o); yield 0.4
    GLib.idle_add(lambda: (OL.edit_wrap_points(win), False)[1]); yield 1.5
    d = dlg("Edit Wrap Points")
    check("Edit Wrap Points dialog", bool(d))
    shot("l8_wrap")
    if d:
        pts = d[0]._points
        note("points", len(pts))
        pts[1][1] = 80; want = (int(pts[1][0]), 80)
        respond("Edit Wrap Points"); yield 0.8
    poly = o.ContourPolyPolygon
    note("contour", (len(poly[0]), o.SurroundContour, [(p.X, p.Y) for p in poly[0]][:3]) if poly else None)
    check("contour saved", poly and len(poly[0]) <= 25 and abs(poly[0][1].Y - 80) <= 1 and o.SurroundContour, "")
def crop():
    o = return_obj[0]
    s0 = (o.Size.Width, o.Size.Height)
    o.Size = DR.bridge.struct("com.sun.star.awt.Size", Width=s0[0], Height=s0[0])  # square frame
    OL.aspect_fill(o); yield 0.4
    c = o.GraphicCrop
    check("Fill crops sides", c.Left > 0 and c.Right > 0, (c.Left, c.Right))
    OL.aspect_fit(o); yield 0.4
    check("Fit restores whole picture", o.GraphicCrop.Left == 0 and abs(o.Size.Width / o.Size.Height - 4/3) < 0.02, (o.Size.Width, o.Size.Height))
    note("glow on picture supported", OL.supports_glow(o))
    docapi.controller(M()).select(o); yield 0.3
    OL.crop_to_shape(win, "ellipse"); yield 1.0
    dp = M().getDrawPage()
    shapes = [dp.getByIndex(i) for i in range(dp.getCount())]
    cs = [x for x in shapes if x.supportsService("com.sun.star.drawing.CustomShape")]
    check("crop to shape made a shape", len(cs) == 1 and M().getGraphicObjects().getCount() == 0, (len(cs), M().getGraphicObjects().getCount()))
    shot("l8_shape")
    if cs:
        ok = OL.set_glow(cs[0], 8, 0x4472C4) and OL.set_soft_edges(cs[0], 5); yield 0.5
        check("glow / soft edges on shape", ok)
        shot("l8_glow")
run_scenarios(layout, wrappts, crop)
