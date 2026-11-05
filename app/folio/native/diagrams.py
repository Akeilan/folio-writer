"""Cork diagrams in Page (K3-08): double-click opens one in Folio Cork, each save there updates
it here; a diagram copied in Cork pastes as one. The format lives in corkembed."""
from .. import corkembed

_open = {}


def edit_selected(view, message):
    """Open the selected picture in Cork when it is a diagram. Returns the editing session."""
    ed = view.ed
    got = ed.object_image()
    objs = ed.selected_objects()
    if not got or not objs or not corkembed.is_diagram(bytes(got[0])):
        return None
    node = objs[0][0]
    old = _open.get((id(ed), node))
    if old is not None and old.running():
        return old
    size0 = [corkembed.png_size(bytes(got[0]))]

    def changed(png):
        if view.ed is not ed:
            return
        prev = [o[0] for o in ed.selected_objects()]
        if not ed.select_object_node(node):
            return
        o = ed.selected_object()
        ed.object_set_image(png, "png")
        new = corkembed.png_size(png)
        if o and new and size0[0]:
            ed.object_resize(new[0] * o["w"] / max(1, size0[0][0]), new[1] * o["h"] / max(1, size0[0][1]))
        size0[0] = new
        if prev:
            ed.select_object_nodes(prev)
        else:
            ed.deselect_object()
        view.objs.refresh()
        view.document_changed()

    s = corkembed.edit(bytes(got[0]), changed, message, on_close=lambda: _open.pop((id(ed), node), None))
    if s is not None:
        _open[(id(ed), node)] = s
    return s
