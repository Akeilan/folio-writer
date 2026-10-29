import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
# 2.32 (W3-08): Options > Save > Embed fonts in the file; embedded fonts used when opened
import os
import re
import struct
import zipfile

from folio.native import embedfonts as EF

MSG = []
win.dialogs.message = lambda text, *a, **k: MSG.append(text)


def renamed(data, family):
    """A copy of a TrueType font calling itself `family` (its name table rewritten)."""
    t = EF._tables(data)
    off, _ln = t[b"name"]
    fmt, count, soff = struct.unpack_from(">HHH", data, off)
    recs = []
    for i in range(count):
        pid, eid, lid, nid, ln, o = struct.unpack_from(">HHHHHH", data, off + 6 + 12 * i)
        s = data[off + soff + o:off + soff + o + ln]
        if nid in (1, 4, 6, 16):
            name = family if nid != 6 else family.replace(" ", "")
            s = name.encode("utf-16-be") if pid in (0, 3) else name.encode("latin-1")
        recs.append((pid, eid, lid, nid, s))
    strings = b""
    table = struct.pack(">HHH", 0, len(recs), 6 + 12 * len(recs))
    for pid, eid, lid, nid, s in recs:
        table += struct.pack(">HHHHHH", pid, eid, lid, nid, len(s), len(strings))
        strings += s
    return EF._rebuild(data, t, {b"name": table + strings})


def files(path):
    z = zipfile.ZipFile(path)
    return {n: z.read(n) for n in z.namelist()}


def a():
    yield 1.0
    ed = E.ed
    ed.type_text("Embedded font sample 123")
    ed.select_all()
    ed.set_font("DejaVu Serif")
    E.view.after_edit(); yield 0.3
    # ---- the Options dialog's Save page shows the three choices for this document
    from folio import options
    src = open(options.__file__).read()
    check("options offer embedding", all(t in src for t in ("Embed fonts in the _file", "Embed only the _characters",
                                                            "Do not embed common _system fonts")))
    # ---- embedding on, common fonts too: the font travels in the file
    ed.set_settings_xml("w:embedTrueTypeFonts", "<w:embedTrueTypeFonts/>")
    ed.set_settings_xml("w:embedSystemFonts", "<w:embedSystemFonts/>")
    out = "/tmp/n40_embed.docx"
    ok = win.save_to(out); yield 1.0
    f = files(out)
    fonts = [n for n in f if n.startswith("word/fonts/")]
    check("saved", ok, MSG)
    check("font embedded", len(fonts) >= 1, list(f)[:20])
    ft = f.get("word/fontTable.xml", b"").decode()
    check("font table names it", re.search(r'<w:font w:name="DejaVu Serif".*?<w:embedRegular r:id="[^"]+" w:fontKey="\{[0-9A-F-]{36}\}"/>', ft, re.S) is not None, ft[-400:])
    check("relationship and content type", b"relationships/font" in f.get("word/_rels/fontTable.xml.rels", b"")
          and b"obfuscatedFont" in f["[Content_Types].xml"])
    key = re.search(r'w:fontKey="(\{[^"]+\})"', ft).group(1)
    data = EF.obfuscate(f[fonts[0]], key)
    check("obfuscated as Word does (and undone)", f[fonts[0]][:4] != data[:4] and data[:4] == b"\x00\x01\x00\x00")
    whole = len(f[fonts[0]])
    # ---- only the characters used: a much smaller font, still valid
    ed.set_settings_xml("w:saveSubsetFonts", "<w:saveSubsetFonts/>")
    ok = win.save_to(out); yield 1.0
    f = files(out)
    fonts = [n for n in f if n.startswith("word/fonts/")]
    check("subset saved", ok and fonts and len(f[fonts[0]]) < whole / 2, (whole, [len(f[n]) for n in fonts]))
    check("subset flag in settings", b"<w:saveSubsetFonts/>" in f["word/settings.xml"])
    # ---- common system fonts left out
    ed.set_settings_xml("w:embedSystemFonts", None)
    ok = win.save_to(out); yield 1.0
    f = files(out)
    check("common fonts not embedded", ok and not [n for n in f if n.startswith("word/fonts/")], [n for n in f if "font" in n])
    # ---- embedding off: earlier fonts taken out
    ed.set_settings_xml("w:embedSystemFonts", "<w:embedSystemFonts/>")
    win.save_to(out); yield 1.0
    check("embedded again", any(n.startswith("word/fonts/") for n in files(out)))
    for tag in ("w:embedTrueTypeFonts", "w:saveSubsetFonts", "w:embedSystemFonts"):
        ed.set_settings_xml(tag, None)
    win.save_to(out); yield 1.0
    f = files(out)
    check("embedding off removes them", not any(n.startswith("word/fonts/") for n in f)
          and b"embedRegular" not in f.get("word/fontTable.xml", b""), [n for n in f if "font" in n])
    ed.mark_saved()
    # ---- a document carrying a font this computer doesn't have: drawn with it
    faces = EF.installed()
    base = faces.get(("dejavu serif", False, False))
    with open(base, "rb") as fh:
        custom = renamed(fh.read(), "Folio Embed Test")
    sample = "/tmp/n40_carries.docx"
    from folio.native import docxbuild as B
    d = B.Doc()
    s = B.section()
    p = B.para("Text in the embedded font")
    p["runs"][0]["rpr"] = {"font": "Folio Embed Test"}
    s["blocks"] = [p]
    d.sections = [s]
    with open(sample, "wb") as fh:
        fh.write(B.to_docx(d))
    EF._write(sample, files(sample), {("Folio Embed Test", False, False): custom})
    check("test font not installed", ("folio embed test", False, False) not in faces)
    win.open_file(sample); yield 2.0
    check("carrying document opens", E.ed is not None and "Text in the embedded font" in str(
        [E.ed.para_text_of(n) for k, n, _t in E.ed.body_blocks() if k == "p"]))
    check("its font is available this session", "Folio" in os.environ.get("FOLIO_FONT_DIRS", "") or
          any("Folio_Embed_Test" in x for dd in os.environ.get("FOLIO_FONT_DIRS", "").split(":") if dd and os.path.isdir(dd)
              for x in os.listdir(dd)), os.environ.get("FOLIO_FONT_DIRS"))
    pdf = "/tmp/n40_carries.pdf"
    E.ed.export_pdf_opts(pdf, [], False, "", "", "", "")
    raw = open(pdf, "rb").read()
    check("drawn with the embedded font", b"FolioEmbedTest" in raw or b"Folio Embed Test" in raw,
          re.findall(rb"/FontName\s*/([^\s/]+)", raw)[:5])
    E.ed.mark_saved()


run_scenarios(a)
