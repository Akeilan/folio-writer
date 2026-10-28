exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
# 2.31: dragging a heading in the Navigation pane moves its section (W2-05)
from gi.repository import Gtk


def body(ed):
    return [t for t in (ed.para_text_of(n) for k, n, _t in ed.body_blocks() if k == "p") if t]


def row_point(tv, path):
    """Screen coordinates of the middle of a tree row."""
    col = tv.get_column(0)
    r = tv.get_cell_area(Gtk.TreePath.new_from_string(path), col)
    wx, wy = tv.convert_bin_window_to_widget_coords(r.x + 20, r.y + r.height // 2)
    top = tv.get_toplevel()
    tx, ty = tv.translate_coordinates(top, wx, wy)
    ox, oy = top.get_window().get_origin()[1:]
    return ox + tx, oy + ty


def a():
    yield 1.0
    focus(); yield 0.2
    fresh(); yield 0.2
    ed = E.ed
    for title, text in (("Alpha", "Alpha text"), ("Beta", "Beta text"), ("Gamma", "Gamma text")):
        win.run(("style", "Heading 1")); T(title + "\n"); yield 0.2
        win.run(("style", "Normal")); T(text + "\n"); yield 0.2
    yield 0.5
    check("document", body(ed)[:6] == ["Alpha", "Alpha text", "Beta", "Beta text", "Gamma", "Gamma text"], body(ed))
    from folio.panes import NavigationPane
    win.toggle_navigation_pane()
    yield 1.0
    nav = win.panes.get(NavigationPane)
    check("navigation pane open", nav is not None and nav.get_mapped(), nav)
    nav.show_headings(); yield 0.8
    tv = nav.htv
    check("three headings", len(nav.hstore) == 3, [r[0] for r in nav.hstore])
    shot("n32_before"); yield 0.2
    # drag Gamma above Alpha with the mouse
    x0, y0 = row_point(tv, "2")
    x1, y1 = row_point(tv, "0")
    X("mousemove", x0, y0); yield 0.3
    X("mousedown", 1); yield 0.3
    for k in range(1, 9):
        X("mousemove", x0, y0 - (y0 - y1 + 4) * k // 8); yield 0.08
    X("mousemove", x1, y1 - 4); yield 0.4
    X("mouseup", 1); yield 1.5
    shot("n32_after"); yield 0.2
    check("Gamma's section moved first", body(ed)[:6] == ["Gamma", "Gamma text", "Alpha", "Alpha text", "Beta", "Beta text"],
          body(ed))
    check("pane follows", [r[0] for r in nav.hstore] == ["Gamma", "Alpha", "Beta"], [r[0] for r in nav.hstore])
    # and back below Beta
    x0, y0 = row_point(tv, "0")
    x1, y1 = row_point(tv, "2")
    X("mousemove", x0, y0); yield 0.3
    X("mousedown", 1); yield 0.3
    for k in range(1, 9):
        X("mousemove", x0, y0 + (y1 - y0 + 4) * k // 8); yield 0.08
    X("mousemove", x1, y1 + 6); yield 0.4
    X("mouseup", 1); yield 1.5
    check("moved after the last heading", body(ed)[:6] == ["Alpha", "Alpha text", "Beta", "Beta text", "Gamma", "Gamma text"],
          body(ed))
    win.focus_document(); yield 0.2
    K("ctrl+z"); yield 0.8
    check("undo puts it back", body(ed)[:2] == ["Gamma", "Gamma text"], body(ed))
    E.ed.mark_saved()


run_scenarios(a)
