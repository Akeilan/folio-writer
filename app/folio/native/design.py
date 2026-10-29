"""Design tab with the new engine: theme colours and fonts (the theme part),
themes, paragraph spacing, and Set as Default."""
import os

from .. import themedata as TD


def _done(win):
    win.engine.view.document_changed()
    try:
        win.design_changed()
    except Exception:
        pass


def colors(win, name):
    cs = TD.COLOR_SCHEMES.get(name)
    if cs and win.engine.ed.set_theme_colors(name, cs):
        _done(win)


def fonts(win, name):
    fs = TD.FONT_SCHEMES.get(name)
    if fs and win.engine.ed.set_theme_fonts(name, fs[0], fs[1]):
        _done(win)


def theme(win, name):
    c, f = TD.THEMES.get(name, ("Standard", "Standard"))
    ed = win.engine.ed
    ed.begin_group("Theme")
    ed.set_theme_colors(c, TD.COLOR_SCHEMES[c])
    ed.set_theme_fonts(f, *TD.FONT_SCHEMES[f])
    ed.end_group()
    _done(win)


def spacing(win, preset):
    before, after, line = TD.SPACING.get(preset, TD.SPACING["default"])
    if win.engine.ed.set_paragraph_spacing(before * 20, after * 20, int(round(line * 2.4))):
        _done(win)


def set_as_default(win):
    if not win.dialogs.confirm("Do you want to set the current style set and theme as the default?\n\n"
                               "New documents will use these settings.", yes="Yes", no="No"):
        return
    app = win.app
    try:
        src = app.normal_template()
    except FileNotFoundError:
        return
    base = os.path.splitext(os.path.basename(src))[0]
    tpl = os.path.splitext(src)[0] + ".docx"
    if not os.path.exists(tpl):
        for d in ("/usr/share/folio-writer/templates",
                  os.path.join(os.path.dirname(__file__), "..", "..", "..", "share", "templates")):
            p = os.path.join(d, base + ".docx")
            if os.path.exists(p):
                tpl = p
                break
    out = os.path.join(os.path.dirname(app.user_template_path()), base + ".docx")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    try:
        win.engine.ed.save_as_template(tpl, out)
    except OSError as e:
        win.dialogs.message("Folio couldn't save the default template.\n\n%s" % e, kind="error")


def _theme_rgb(ed, slot, fallback):
    try:
        return ed.theme_colors().get(slot, fallback)
    except Exception:
        return fallback


def style_set(win, name):
    """Design > Document Formatting: a style set restyles Title and the headings (W3-04:
    with Folio's engine, through the document's own styles and theme colours)."""
    from ..modelapi import STYLE_SETS
    spec = STYLE_SETS.get(name)
    if spec is None:
        return
    ed = win.engine.ed
    ids = {n: i for i, n in ed.paragraph_styles()}
    accent = _theme_rgb(ed, "accent1", 0x4472C4)
    text2 = _theme_rgb(ed, "dk2", 0x44546A)
    colours = {"accent": (accent, "accent1", None), "h1": (TD.shade(accent, 0.75), "accent1", "BF"),
               "h2": (TD.shade(accent, 0.75), "accent1", "BF"), "title": (0x000000, "text1", None),
               "white": (0xFFFFFF, "background1", None), "gray": (0x595959, "text1", "A6")}
    _ = text2
    ed.begin_group("Style Set")
    try:
        for style, d in spec.items():
            sid = ids.get(style)
            if not sid:
                continue
            run = [("w:sz", [("w:val", str(int(d["size"] * 2)))]),
                   ("w:szCs", [("w:val", str(int(d["size"] * 2)))]),
                   ("w:b", [] if d.get("bold") else [("w:val", "0")]),
                   ("w:i", [] if d.get("italic") else [("w:val", "0")]),
                   ("w:caps", [] if d.get("caps") else [("w:val", "0")])]
            c = colours.get(d.get("color"))
            if c:
                attrs = [("w:val", "%06X" % c[0]), ("w:themeColor", c[1])]
                if c[2]:
                    attrs.append(("w:themeShade", c[2]))
                run.append(("w:color", attrs))
            else:
                run.append(("w:color", [("w:val", "auto")]))
            ed.style_apply_run(sid, run)
            para = [("w:jc", [("w:val", "center" if d.get("align") == "center" else "left")])]
            if d.get("shade"):
                sc = colours.get(d["shade"], (accent, "accent1", None))
                para.append(("w:shd", [("w:val", "clear"), ("w:color", "auto"), ("w:fill", "%06X" % sc[0])]))
            else:
                para.append(("w:shd", None))
            if d.get("border"):
                side, width, ckey = d["border"]
                bc = colours.get(ckey, (0x000000, None, None))[0] if ckey else 0x000000
                sz = str(max(2, int(round(width / 2540.0 * 72 * 8))))     # 1/100 mm -> eighths of a point
                para.append(("w:pBdr", [("w:%s" % side, "single", sz, "%06X" % bc)]))
            else:
                para.append(("w:pBdr", None))
            _apply_para(ed, sid, para)
    finally:
        ed.end_group()
    _set_meta(win, "StyleSet", name)
    _done(win)


def _apply_para(ed, sid, edits):
    simple = [(n, a) for n, a in edits if n != "w:pBdr"]
    ed.style_apply_para(sid, simple)
    for n, a in edits:
        if n == "w:pBdr":
            if a is None:
                ed.style_apply_para(sid, [("w:pBdr", None)])
            else:
                for side, kind, sz, color in a:
                    ed.style_apply_para_attrs(sid, "w:pBdr/" + side, [("w:val", kind), ("w:sz", sz),
                                                                      ("w:space", "1"), ("w:color", color)])


def _set_meta(win, key, value):
    """A document setting the Design tab keeps (the style set's name)."""
    try:
        from ..modelapi import _set_doc_setting
        _set_doc_setting(win.dialogs.model, key, value)
    except Exception:
        pass


def current_style_set(win):
    try:
        from ..modelapi import current_style_set as cur
        return cur(win.dialogs.model)
    except Exception:
        return "Default"
