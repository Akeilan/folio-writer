"""The fonts the Font box lists: families that cover English and aren't built
for another script, without symbol, emoji and fallback fonts."""
import re

_FONT_JUNK = re.compile(
    r"Emoji|Unifont|\bMath\b|Fallback|CJK|WenQuanYi|^IPA|^Droid Sans (?!Mono$)|"
    r"^Noto (?!(Sans|Serif)( Mono| Display)?$)|^Latin Modern (Roman|Sans|Mono) .|^LM (?!(Roman|Sans|Mono) 10$)|^Noto Sans (Mono|Display) \w|^OpenSymbol$|"
    r"^(Lohit|Kacst|Samyak|Sawasdee|Tlwg|Garuda|Kinnari|Laksaman|Loma|Norasi|Purisa|"
    r"Umpush|Waree|Khmer OS|Padauk|Phetsarath|Mukti|Pothana|Vemana|Rachana|Meera|"
    r"Gargi|Nakula|Sahadeva|Kalimati|Jamrul|Likhan|Saab|Suruma|Chandas|Abyssinica)")

_SCRIPT_LANGS = {"ja", "ko", "zh-cn", "zh-tw"}
_LATIN_FONTS = []


def latin_font_families():
    """Family names (all aliases) of fonts covering English that aren't
    built for another script. None when fontconfig can't be asked."""
    if _LATIN_FONTS:
        return _LATIN_FONTS[0]
    import subprocess
    try:
        out = subprocess.run(["fc-list", ":lang=en", "family", "lang"], capture_output=True,
                             text=True, timeout=10).stdout
    except Exception:
        out = ""
    ok, bad = set(), set()
    for line in out.splitlines():
        fam, _, langs = line.partition(":lang=")
        names = [f.replace("\\", "").strip() for f in fam.split(",") if f.strip()]
        langset = set(langs.split("|"))
        target = bad if langset & _SCRIPT_LANGS and not any(
            n.startswith(("DejaVu", "Free", "Noto Sans", "Noto Serif")) for n in names) else ok
        target.update(names)
    if not ok:
        ok = _pango_families()
    _LATIN_FONTS.append(ok - bad if ok else None)
    return _LATIN_FONTS[0]


def _pango_families():
    """Without fc-list, ask Pango for the installed families."""
    try:
        import gi
        gi.require_version("PangoCairo", "1.0")
        from gi.repository import PangoCairo
        return {f.get_name() for f in PangoCairo.FontMap.get_default().list_families()}
    except Exception:
        return set()
