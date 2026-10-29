"""The Borders drop-down, as in the original: it works on the selected
paragraphs, or on the selected table cells (outside, inside, inside
horizontal / vertical, diagonal)."""



def apply_win(win, which):
    """The Borders menu for a window (either engine)."""
    from .native import tables
    tables.borders_menu(win, which)
    return


def horizontal_line(win):
    """A paragraph of its own with a line across, as the original inserts."""
    ed = win.engine.ed
    p0 = ed.caret_pos()[0]
    for _i in range(500):
        ed.move_caret("end", False)
        c = ed.caret_pos()
        ed.move_caret("right", False)
        n = ed.caret_pos()
        if n[0] != p0 or n == c:
            if n != c:
                ed.move_caret("left", False)
            break
    line = [("w:val", "single"), ("w:sz", "12"), ("w:space", "1"), ("w:color", "A0A0A0")]
    ed.begin_group("Horizontal Line")
    ed.type_text("\n")
    ed.set_borders("paras", [(s, None) for s in ("top", "left", "right", "between")] + [("bottom", line)])
    ed.type_text("\n")
    ed.set_borders("paras", [(s, None) for s in ("top", "left", "bottom", "right", "between")])
    ed.end_group()
    win.engine.view.after_edit()
    return
