"""Files Folio reads itself without any converter: OpenDocument text, Word 97-2003 and
Rich Text Format. Each is read into the shared document model and written as a .docx for
the engine."""
import os

ODF = (".odt", ".ott", ".fodt")
WORD97 = (".doc", ".dot")
RTF = (".rtf",)


def handles(path):
    ext = os.path.splitext(path)[1].lower()
    return ext in ODF or ext in WORD97 or ext in RTF or _sniff_rtf(path)


def _sniff_rtf(path):
    """A file that is RTF whatever its name says (Word saves .doc files as RTF at times)."""
    try:
        with open(path, "rb") as fh:
            return fh.read(5) == b"{\\rtf"
    except OSError:
        return False


def read(path):
    import sys
    sys.setrecursionlimit(max(sys.getrecursionlimit(), 20000))
    ext = os.path.splitext(path)[1].lower()
    if ext in ODF:
        from . import odfread
        return odfread.read(path)
    if ext in RTF or _sniff_rtf(path):
        from . import rtfread
        return rtfread.read(path)
    from . import docread
    return docread.read(path)


def to_docx(path, out_path):
    from . import docxbuild
    doc = read(path)
    data = docxbuild.to_docx(doc)
    with open(out_path, "wb") as fh:
        fh.write(data)
    to_docx.dropped = dict(getattr(doc, "dropped", {}) or {})
    return out_path


to_docx.dropped = {}


def dropped_note(dropped):
    """What to tell the user about what a converted file lost (W5-04)."""
    n = (dropped or {}).get("objects") or 0
    if not n:
        return None
    return ("This file holds %d embedded object%s - a chart or a drawing made in another "
            "program. %s can't show %s: the file carries only a preview picture that no "
            "program outside the one that made it can read. The rest of the document is here."
            % (n, "" if n == 1 else "s", "Folio Page", "it" if n == 1 else "them"))
