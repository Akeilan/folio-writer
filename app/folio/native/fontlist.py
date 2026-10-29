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
