"""Layout > Margins, Orientation, Size and Columns with the new engine:
the section's w:sectPr (the caret's section), and mirror margins."""

TW_PER_MM100 = 1440.0 / 2540.0


def _tw(mm100):
    return str(int(round(mm100 * TW_PER_MM100)))


def _apply(win, label, changes):
    ed = win.engine.ed
    sec = ed.current_section()
    ed.begin_group(label)
    try:
        for el, attr, val in changes:
            ed.section_attr(sec, el, attr, val, label)
    finally:
        ed.end_group()
    win.engine.view.document_changed()


def margins(win, top, bottom, left, right, mirrored=False):
    """Margins in 1/100 mm; mirrored: inside / outside on facing pages."""
    ed = win.engine.ed
    ed.begin_group("Margins")
    _apply(win, "Margins", [("w:pgMar", "w:top", _tw(top)), ("w:pgMar", "w:bottom", _tw(bottom)),
                            ("w:pgMar", "w:left", _tw(left)), ("w:pgMar", "w:right", _tw(right))])
    ed.set_setting("mirrorMargins", bool(mirrored))
    ed.end_group()
    win.engine.view.document_changed()


def orientation(win, landscape):
    ed = win.engine.ed
    ps = ed.page_setup(ed.current_section())
    if ps is None:
        return
    w, h = ps["width"], ps["height"]
    if bool(landscape) == (w > h):
        return
    _apply(win, "Orientation", [("w:pgSz", "w:w", str(h)), ("w:pgSz", "w:h", str(w)),
                                ("w:pgSz", "w:orient", "landscape" if landscape else None)])


def paper(win, width, height):
    """Paper size in 1/100 mm, in the current orientation."""
    ed = win.engine.ed
    ps = ed.page_setup(ed.current_section())
    landscape = bool(ps and ps["width"] > ps["height"])
    w, h = (max(width, height), min(width, height)) if landscape else (min(width, height), max(width, height))
    _apply(win, "Size", [("w:pgSz", "w:w", _tw(w)), ("w:pgSz", "w:h", _tw(h))])


def columns(win, n, space_tw=720):
    _apply(win, "Columns", [("w:cols", "w:num", str(int(n)) if int(n) > 1 else None),
                            ("w:cols", "w:space", str(space_tw))])
