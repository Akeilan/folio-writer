"""Document operations the dialogs and panes use, over the document model Folio's engine
offers them (native.uno_model.NativeModel: styles, the view cursor, document properties and
settings), plus the tables they share (languages, style sets, theme fonts and colours).
Lengths are in 1/100 mm unless stated otherwise. (W3-04: what remained of the old engine's
interface, without it.)"""
import datetime
import re

from . import themedata as _TD

MM100_PER_INCH = 2540


def inch(v):
    return int(round(v * MM100_PER_INCH))


def pt(v):
    return int(round(v * 2540 / 72))


def to_pt(mm100):
    return mm100 * 72 / 2540.0


# ------------------------------------------------------------------ basics


def controller(m):
    return m.getCurrentController()


def read_cursor(m):
    """The text cursor for reading (page style, language, table...). Unlike
    view_cursor it never changes the selection, so a selected picture stays
    selected."""
    return controller(m).getViewCursor()


def view_cursor(m):
    """The text cursor (with Folio's engine an object selection needs no escaping first)."""
    return controller(m).getViewCursor()

def para_styles(m):
    return m.getStyleFamilies().getByName("ParagraphStyles")


def char_styles(m):
    return m.getStyleFamilies().getByName("CharacterStyles")


def statistics(m):
    stats = {p.Name: p.Value for p in m.getDocumentProperties().DocumentStatistics}
    text = m.getText().getString()
    stats["LineCount"] = None
    try:
        vc = view_cursor(m)
        stats["Page"] = vc.getPage()
    except Exception:
        pass
    stats["Text"] = text
    return stats


def count_text(text):
    words = len(re.findall(r"\S+", text))
    chars = len(text.replace("\n", "").replace("\r", ""))
    nospace = len(re.sub(r"\s", "", text))
    paras = len([p for p in re.split(r"[\r\n]+", text) if p.strip()])
    return {"words": words, "chars": chars, "nospace": nospace, "paras": paras}


# ------------------------------------------------------------ properties


def doc_properties(m):
    p = m.getDocumentProperties()

    def dt(d):
        try:
            if d.Year:
                return datetime.datetime(d.Year, d.Month, d.Day, d.Hours, d.Minutes)
        except Exception:
            pass
        return None
    return {"title": p.Title, "subject": p.Subject, "author": p.Author,
            "keywords": ", ".join(p.Keywords), "comments": p.Description,
            "modified_by": p.ModifiedBy, "created": dt(p.CreationDate),
            "modified": dt(p.ModificationDate), "printed": dt(p.PrintDate),
            "revision": p.EditingCycles, "editing_minutes": p.EditingDuration // 60,
            "template": p.TemplateName}


def set_doc_property(m, key, value):
    p = m.getDocumentProperties()
    if key == "title":
        p.Title = value
    elif key == "subject":
        p.Subject = value
    elif key == "author":
        p.Author = value
    elif key == "keywords":
        p.Keywords = tuple(k.strip() for k in value.split(",") if k.strip())
    elif key == "comments":
        p.Description = value


def selected_link(m):
    vc = view_cursor(m)
    try:
        return vc.HyperLinkURL or ""
    except Exception:
        return ""


STYLE_PROPS = ("CharFontName", "CharHeight", "CharWeight", "CharPosture", "CharColor",
               "CharUnderline", "ParaAdjust", "ParaTopMargin", "ParaBottomMargin",
               "ParaLeftMargin", "ParaRightMargin", "ParaFirstLineIndent")


def style_info(m, name, family="ParagraphStyles"):
    fam = m.getStyleFamilies().getByName(family)
    if not fam.hasByName(name):
        return None
    st = fam.getByName(name)
    info = {"name": st.Name, "display": st.DisplayName, "parent": st.ParentStyle,
            "in_use": st.isInUse(), "user": st.isUserDefined()}
    for p in STYLE_PROPS:
        try:
            info[p] = getattr(st, p)
        except Exception:
            pass
    try:
        info["follow"] = st.FollowStyle
        ls = st.ParaLineSpacing
        info["line_mode"], info["line_height"] = ls.Mode, ls.Height
    except Exception:
        pass
    return info


def set_style(m, name, family="ParagraphStyles", **props):
    fam = m.getStyleFamilies().getByName(family)
    st = fam.getByName(name)
    for k, v in props.items():
        if k == "line":
            mode, height = v
            ls = st.ParaLineSpacing
            ls.Mode, ls.Height = mode, height
            st.ParaLineSpacing = ls
        else:
            setattr(st, k, v)


def new_style(m, name, based_on="Standard", follow=None, family="ParagraphStyles",
              from_selection=True, **props):
    fam = m.getStyleFamilies().getByName(family)
    if not fam.hasByName(name):
        svc = "com.sun.star.style.ParagraphStyle" if family == "ParagraphStyles" \
            else "com.sun.star.style.CharacterStyle"
        st = m.createInstance(svc)
        fam.insertByName(name, st)
    st = fam.getByName(name)
    if based_on:
        try:
            st.ParentStyle = based_on
        except Exception:
            pass
    if follow and family == "ParagraphStyles":
        st.FollowStyle = follow
    if from_selection:
        vc = view_cursor(m)
        for p in STYLE_PROPS:
            if family == "CharacterStyles" and p.startswith("Para"):
                continue
            try:
                setattr(st, p, getattr(vc, p))
            except Exception:
                pass
    set_style(m, name, family, **props) if props else None
    vc = view_cursor(m)
    if family == "ParagraphStyles":
        vc.ParaStyleName = name
    else:
        vc.CharStyleName = name
    return name


def style_names(m, family="ParagraphStyles", used_only=False):
    fam = m.getStyleFamilies().getByName(family)
    out = []
    for n in fam.getElementNames():
        st = fam.getByName(n)
        if used_only and not st.isInUse():
            continue
        out.append((n, st.DisplayName))
    return out


# document-wide paragraph spacing presets (Design > Paragraph Spacing)


SPACING_PRESETS = {
    "none": (0, 0, 100),
    "compact": (0, 4, 100),
    "tight": (0, 6, 100),
    "open": (0, 10, 115),
    "relaxed": (0, 6, 150),
    "double": (0, 8, 200),
    "default": (0, 8, 108),
}


FONT_PAIRS = dict(_TD.FONT_SCHEMES)

# name: heading 1, heading 2, title, accent (the classic engine's use of a scheme)


COLOR_SETS = {k: (_TD.shade(v[4], 0.75), _TD.shade(v[4], 0.75), v[0], v[4])
              for k, v in _TD.COLOR_SCHEMES.items()}


def _doc_setting(m, key, default=None):
    try:
        ud = m.getDocumentProperties().getUserDefinedProperties()
        return ud.getPropertyValue(key)
    except Exception:
        return default


def _set_doc_setting(m, key, value):
    try:
        ud = m.getDocumentProperties().getUserDefinedProperties()
        if ud.getPropertySetInfo().hasPropertyByName(key):
            ud.setPropertyValue(key, value)
        else:
            ud.addProperty(key, 128, value)       # REMOVEABLE
    except Exception:
        pass


def current_color_set(m):
    v = _doc_setting(m, "ThemeColors", "Blue")
    return v if v in COLOR_SETS else "Blue"


def current_style_set(m):
    v = _doc_setting(m, "StyleSet", "Default")
    return v if v in STYLE_SETS else "Default"


STYLE_SETS = {
    "Default": {
        "Title": dict(size=28, color="title"),
        "Heading 1": dict(size=16, color="h1"),
        "Heading 2": dict(size=13, color="h2")},
    "Basic (Elegant)": {
        "Title": dict(size=26, caps=True, align="center"),
        "Heading 1": dict(size=14, caps=True, border=("bottom", 18, None)),
        "Heading 2": dict(size=12, caps=True)},
    "Basic (Simple)": {
        "Title": dict(size=26, caps=True, color="accent"),
        "Heading 1": dict(size=14, caps=True, color="accent"),
        "Heading 2": dict(size=12, caps=True, color="h2")},
    "Basic (Stylish)": {
        "Title": dict(size=28, color="accent"),
        "Heading 1": dict(size=14, bold=True, color="h1"),
        "Heading 2": dict(size=12, bold=True)},
    "Casual": {
        "Title": dict(size=30, color="accent"),
        "Heading 1": dict(size=15, color="accent"),
        "Heading 2": dict(size=12, italic=True, color="h2")},
    "Centered": {
        "Title": dict(size=26, caps=True, align="center", color="h1"),
        "Heading 1": dict(size=14, caps=True, align="center", color="h1"),
        "Heading 2": dict(size=12, align="center", color="h2")},
    "Lines (Distinctive)": {
        "Title": dict(size=28, border=("bottom", 53, None)),
        "Heading 1": dict(size=14, bold=True, border=("bottom", 18, None)),
        "Heading 2": dict(size=12, bold=True)},
    "Lines (Simple)": {
        "Title": dict(size=26, color="h1"),
        "Heading 1": dict(size=14, border=("top", 18, "accent"), color="h1"),
        "Heading 2": dict(size=12, color="h2")},
    "Lines (Stylish)": {
        "Title": dict(size=28, color="accent", border=("bottom", 35, "accent")),
        "Heading 1": dict(size=14, color="h1", border=("bottom", 18, "accent")),
        "Heading 2": dict(size=12, color="h2")},
    "Minimalist": {
        "Title": dict(size=24, color="gray"),
        "Heading 1": dict(size=13, bold=True),
        "Heading 2": dict(size=11, bold=True, color="gray")},
    "Shaded": {
        "Title": dict(size=26, color="white", shade="accent"),
        "Heading 1": dict(size=14, caps=True, color="white", shade="h1"),
        "Heading 2": dict(size=12, caps=True, color="h1")},
}


def _set_color(m, key):
    h1, h2, title, accent = COLOR_SETS[current_color_set(m)]
    return {"title": title, "h1": h1, "h2": h2, "accent": accent, "white": 0xFFFFFF,
            "gray": 0x595959, None: -1}.get(key, -1)


def style_set_props(m, name, colors=None):
    """Resolved properties per style: {style: dict(...)} with colours as ints."""
    out = {}
    for st, d in STYLE_SETS[name].items():
        e = dict(d)
        e["color"] = _set_color(m, d.get("color")) if m is not None else d.get("color")
        if d.get("shade"):
            e["shade"] = _set_color(m, d["shade"]) if m is not None else d["shade"]
        if d.get("border"):
            side, w, c = d["border"]
            e["border"] = (side, w, _set_color(m, c) if (m is not None and c) else 0x000000)
        out[st] = e
    return out


THEMES = dict(_TD.THEMES)


MATH_TEXT_FONT = ["Caladea"]


WORD_RE = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)*", re.UNICODE)


LANGUAGES = [
    ("English (United States)", "en", "US"), ("English (United Kingdom)", "en", "GB"),
    ("English (Australia)", "en", "AU"), ("English (Canada)", "en", "CA"),
    ("English (India)", "en", "IN"), ("English (Ireland)", "en", "IE"),
    ("English (New Zealand)", "en", "NZ"), ("English (South Africa)", "en", "ZA"),
    ("Danish", "da", "DK"), ("Dutch (Netherlands)", "nl", "NL"), ("Dutch (Belgium)", "nl", "BE"),
    ("Finnish", "fi", "FI"), ("French (France)", "fr", "FR"), ("French (Canada)", "fr", "CA"),
    ("German (Germany)", "de", "DE"), ("German (Austria)", "de", "AT"),
    ("German (Switzerland)", "de", "CH"), ("Greek", "el", "GR"), ("Hungarian", "hu", "HU"),
    ("Italian (Italy)", "it", "IT"), ("Norwegian (Bokmål)", "nb", "NO"), ("Polish", "pl", "PL"),
    ("Portuguese (Brazil)", "pt", "BR"), ("Portuguese (Portugal)", "pt", "PT"),
    ("Romanian", "ro", "RO"), ("Russian", "ru", "RU"), ("Spanish (Spain)", "es", "ES"),
    ("Spanish (Mexico)", "es", "MX"), ("Swedish (Sweden)", "sv", "SE"), ("Turkish", "tr", "TR"),
    ("Ukrainian", "uk", "UA"),
]


def language_name(code):
    """'en-US' -> 'English (United States)'."""
    code = (code or "").replace("_", "-")
    for name, l, c in LANGUAGES:
        if code in ("%s-%s" % (l, c), l):
            return name
    return code


def has_dictionary(lang, country):
    try:
        import enchant
        return any(enchant.dict_exists(t) for t in ("%s_%s" % (lang, country), lang))
    except Exception:
        return False
