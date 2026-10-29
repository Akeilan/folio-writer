"""Fonts embedded in the file (W3-08), as Word does it: File > Options > Save > "Embed fonts
in the file", with "Embed only the characters used in the document" and "Do not embed
common system fonts".

A .docx keeps each embedded face as word/fonts/fontN.odttf, obfuscated with the key named
in word/fontTable.xml (ECMA-376 Part 1, 17.8.1), and settings.xml says
w:embedTrueTypeFonts (and w:saveSubsetFonts, w:embedSystemFonts). Opening such a file makes
its fonts available to the engine for this session, so the document looks as it was made
even where the font isn't installed."""
import os
import re
import shutil
import struct
import subprocess
import tempfile
import uuid
import zipfile

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
REL_FONT = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/font"
CT_FONT = "application/vnd.openxmlformats-officedocument.obfuscatedFont"
FACES = (("embedRegular", False, False), ("embedBold", True, False), ("embedItalic", False, True),
         ("embedBoldItalic", True, True))
# fonts every computer has: left out with "Do not embed common system fonts"
COMMON = {"arial", "arial black", "calibri", "calibri light", "cambria", "cambria math", "candara",
          "comic sans ms", "consolas", "constantia", "corbel", "courier new", "georgia", "impact",
          "lucida console", "lucida sans unicode", "microsoft sans serif", "palatino linotype",
          "segoe ui", "segoe ui symbol", "symbol", "tahoma", "times new roman", "trebuchet ms",
          "verdana", "webdings", "wingdings", "aptos", "liberation sans", "liberation serif",
          "liberation mono", "dejavu sans", "dejavu serif", "dejavu sans mono", "carlito",
          "caladea", "noto sans", "noto serif", "ubuntu", "opensymbol"}


# ------------------------------------------------------------------ obfuscation
def _key(guid):
    h = re.sub(r"[^0-9A-Fa-f]", "", guid)
    if len(h) != 32:
        raise ValueError("bad font key")
    return bytes(int(h[30 - 2 * i:32 - 2 * i], 16) for i in range(16))


def obfuscate(data, guid):
    """The first 32 bytes XORed with the key (the same operation undoes it)."""
    k = _key(guid)
    head = bytes(b ^ k[i % 16] for i, b in enumerate(data[:32]))
    return head + data[32:]


# ------------------------------------------------------------------ the fonts on this computer
_FACES = None


def installed():
    """{(family lower, bold, italic): file} for the TrueType faces fontconfig knows."""
    global _FACES
    if _FACES is not None:
        return _FACES
    _FACES = {}
    try:
        out = subprocess.run(["fc-list", "--format", "%{family}\t%{style}\t%{weight}\t%{slant}\t%{file}\n"],
                             capture_output=True, text=True, timeout=30).stdout
    except (OSError, subprocess.SubprocessError):
        return _FACES
    best = {}
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) != 5:
            continue
        fams, _style, weight, slant, path = parts
        if not path.lower().endswith(".ttf"):
            continue
        try:
            w = int(weight.split()[0])
            italic = int(slant.split()[0]) > 0
        except ValueError:
            continue
        bold = w >= 180
        # the face nearest Regular (80) or Bold (200) of its kind
        dist = abs(w - (200 if bold else 80))
        for fam in fams.split(","):
            k = (fam.strip().lower(), bold, italic)
            if k not in best or dist < best[k][0]:
                best[k] = (dist, path)
    for k, (_d, path) in best.items():
        _FACES[k] = path
    return _FACES


def embeddable(data):
    """False when the font's licence (OS/2 fsType) forbids embedding it."""
    tables = _tables(data)
    os2 = tables.get(b"OS/2")
    if not os2 or os2[1] < 10:
        return True
    fs = struct.unpack_from(">H", data, os2[0] + 8)[0]
    if fs & 0x0200:          # bitmap embedding only
        return False
    return not (fs & 0x000F) == 0x0002   # restricted licence


def _tables(data):
    if len(data) < 12:
        return {}
    n = struct.unpack_from(">H", data, 4)[0]
    out = {}
    for i in range(n):
        o = 12 + 16 * i
        if o + 16 > len(data):
            break
        tag, _chk, off, ln = struct.unpack_from(">4sIII", data, o)
        out[tag] = (off, ln)
    return out


# ------------------------------------------------------------------ subsetting
def _cmap(data, tables):
    """{codepoint: glyph id} from the font's Unicode cmap (format 4 or 12)."""
    off, _ln = tables[b"cmap"]
    n = struct.unpack_from(">H", data, off + 2)[0]
    best = None
    for i in range(n):
        pid, eid, sub = struct.unpack_from(">HHI", data, off + 4 + 8 * i)
        fmt = struct.unpack_from(">H", data, off + sub)[0]
        if (pid, eid) in ((3, 10), (0, 4), (0, 6)) and fmt == 12:
            best = (off + sub, 12)
            break
        if (pid, eid) in ((3, 1), (0, 3), (0, 1), (3, 0)) and fmt == 4 and best is None:
            best = (off + sub, 4)
    out = {}
    if best is None:
        return out
    o, fmt = best
    if fmt == 4:
        segx2 = struct.unpack_from(">H", data, o + 6)[0]
        seg = segx2 // 2
        ends = o + 14
        starts = ends + segx2 + 2
        deltas = starts + segx2
        ranges = deltas + segx2
        for s in range(seg):
            end = struct.unpack_from(">H", data, ends + 2 * s)[0]
            start = struct.unpack_from(">H", data, starts + 2 * s)[0]
            delta = struct.unpack_from(">h", data, deltas + 2 * s)[0]
            ro = struct.unpack_from(">H", data, ranges + 2 * s)[0]
            for c in range(start, min(end, 0xFFFE) + 1):
                if ro:
                    p = ranges + 2 * s + ro + 2 * (c - start)
                    g = struct.unpack_from(">H", data, p)[0] if p + 2 <= len(data) else 0
                    if g:
                        g = (g + delta) & 0xFFFF
                else:
                    g = (c + delta) & 0xFFFF
                if g:
                    out[c] = g
    else:
        ngroups = struct.unpack_from(">I", data, o + 12)[0]
        for k in range(ngroups):
            a, z, g0 = struct.unpack_from(">III", data, o + 16 + 12 * k)
            for c in range(a, min(z, a + 0x10000) + 1):
                out[c] = g0 + (c - a)
    return out


def subset(data, chars):
    """The font with only the glyphs the given characters need (and their components):
    the other glyphs are emptied, so glyph numbers and every other table stay valid."""
    t = _tables(data)
    if b"glyf" not in t or b"loca" not in t or b"head" not in t or b"cmap" not in t or b"gvar" in t:
        return data                         # not plain TrueType outlines (or variable): kept whole
    head = t[b"head"][0]
    long_loca = struct.unpack_from(">h", data, head + 50)[0] == 1
    nglyphs = struct.unpack_from(">H", data, t[b"maxp"][0] + 4)[0] if b"maxp" in t else 0
    loff = t[b"loca"][0]
    if long_loca:
        loca = list(struct.unpack_from(">%dI" % (nglyphs + 1), data, loff))
    else:
        loca = [2 * v for v in struct.unpack_from(">%dH" % (nglyphs + 1), data, loff)]
    goff = t[b"glyf"][0]
    cmap = _cmap(data, t)
    keep = {0}
    for ch in chars:
        g = cmap.get(ord(ch))
        if g:
            keep.add(g)
    # composite glyphs: keep their parts
    todo = list(keep)
    while todo:
        g = todo.pop()
        if g >= nglyphs:
            continue
        a, z = goff + loca[g], goff + loca[g + 1]
        if z - a < 10 or struct.unpack_from(">h", data, a)[0] >= 0:
            continue
        p = a + 10
        while p + 4 <= z:
            flags, comp = struct.unpack_from(">HH", data, p)
            if comp not in keep:
                keep.add(comp)
                todo.append(comp)
            p += 4 + (4 if flags & 1 else 2)
            p += 8 if flags & 0x80 else 4 if flags & 0x40 else 2 if flags & 8 else 0
            if not flags & 0x20:
                break
    glyf = bytearray()
    new_loca = [0]
    for g in range(nglyphs):
        if g in keep:
            glyf += data[goff + loca[g]:goff + loca[g + 1]]
            while len(glyf) % 4:
                glyf.append(0)
        new_loca.append(len(glyf))
    if long_loca:
        loca_b = struct.pack(">%dI" % len(new_loca), *new_loca)
    else:
        loca_b = struct.pack(">%dH" % len(new_loca), *[v // 2 for v in new_loca])
    return _rebuild(data, t, {b"glyf": bytes(glyf), b"loca": loca_b})


def _checksum(b):
    b = b + b"\x00" * (-len(b) % 4)
    return sum(struct.unpack(">%dI" % (len(b) // 4), b)) & 0xFFFFFFFF


def _rebuild(data, tables, replace):
    tags = sorted(tables)
    n = len(tags)
    body = bytearray()
    entries = []
    off = 12 + 16 * n
    for tag in tags:
        if tag in replace:
            blob = replace[tag]
        else:
            o, ln = tables[tag]
            blob = data[o:o + ln]
        if tag == b"head":
            blob = blob[:8] + b"\x00\x00\x00\x00" + blob[12:]
        entries.append((tag, _checksum(blob), off + len(body), len(blob)))
        body += blob
        while len(body) % 4:
            body.append(0)
    es = 1
    while es * 2 <= n:
        es *= 2
    hdr = data[:4] + struct.pack(">HHHH", n, es * 16, es.bit_length() - 1, n * 16 - es * 16)
    hdr += b"".join(struct.pack(">4sIII", *e) for e in entries)
    out = bytearray(hdr + body)
    head = next((e for e in entries if e[0] == b"head"), None)
    if head:
        adj = (0xB1B0AFBA - _checksum(bytes(out))) & 0xFFFFFFFF
        struct.pack_into(">I", out, head[2] + 8, adj)
    return bytes(out)


# ------------------------------------------------------------------ the .docx package
def _flags(settings_xml):
    on = lambda name: bool(re.search(r"<w:%s(\s+w:val=\"(1|true|on)\")?\s*/>" % name, settings_xml))  # noqa: E731
    return on("embedTrueTypeFonts"), on("saveSubsetFonts"), on("embedSystemFonts")


def _used(z):
    """{(family, bold, italic): characters} the document's text uses, roughly per face."""
    import xml.etree.ElementTree as ET
    q = "{%s}" % W
    styles_font = {}
    default_font = None
    try:
        st = ET.fromstring(z.read("word/styles.xml"))
        d = st.find(q + "docDefaults/" + q + "rPrDefault/" + q + "rPr/" + q + "rFonts")
        if d is not None:
            default_font = d.get(q + "ascii")
        for s in st.findall(q + "style"):
            f = s.find(q + "rPr/" + q + "rFonts")
            if f is not None and f.get(q + "ascii"):
                styles_font[s.get(q + "styleId")] = f.get(q + "ascii")
    except (KeyError, ET.ParseError):
        pass
    used = {}
    for name in z.namelist():
        if not re.match(r"word/(document|header\d*|footer\d*|footnotes|endnotes|comments)\.xml$", name):
            continue
        root = ET.fromstring(z.read(name))
        for p in root.iter(q + "p"):
            ps = p.find(q + "pPr/" + q + "pStyle")
            pfont = styles_font.get(ps.get(q + "val")) if ps is not None else None
            for r in p.iter(q + "r"):
                rpr = r.find(q + "rPr")
                font, bold, italic = pfont or default_font, False, False
                if rpr is not None:
                    f = rpr.find(q + "rFonts")
                    if f is not None and f.get(q + "ascii"):
                        font = f.get(q + "ascii")
                    cs = rpr.find(q + "rStyle")
                    if cs is not None and styles_font.get(cs.get(q + "val")) and (f is None):
                        font = styles_font[cs.get(q + "val")]
                    b = rpr.find(q + "b")
                    bold = b is not None and b.get(q + "val") not in ("0", "false")
                    i = rpr.find(q + "i")
                    italic = i is not None and i.get(q + "val") not in ("0", "false")
                text = "".join(t.text or "" for t in r.iter(q + "t"))
                if font and text:
                    used.setdefault((font, bold, italic), set()).update(text)
    return used


def apply(path):
    """After a .docx is saved: embed its fonts when its settings ask for it, or take out
    fonts embedded earlier when they no longer do. Returns the families embedded."""
    try:
        z = zipfile.ZipFile(path)
    except (OSError, zipfile.BadZipFile):
        return []
    with z:
        names = z.namelist()
        settings = z.read("word/settings.xml").decode("utf-8", "replace") if "word/settings.xml" in names else ""
        embed, sub, system = _flags(settings)
        had = any(n.startswith("word/fonts/") for n in names)
        if not embed and not had:
            return []
        parts = {n: z.read(n) for n in names}
    fonts = {}
    done = []
    if embed:
        faces = installed()
        used = _used(zipfile.ZipFile(path))
        for (fam, bold, italic), chars in sorted(used.items()):
            if not system and fam.lower() in COMMON:
                continue
            f = faces.get((fam.lower(), bold, italic)) or (faces.get((fam.lower(), False, False)) if not (bold or italic) else None)
            if not f:
                continue
            try:
                with open(f, "rb") as fh:
                    data = fh.read()
            except OSError:
                continue
            if not embeddable(data):
                continue
            if sub:
                try:
                    data = subset(data, chars | set(" 0123456789"))
                except (struct.error, KeyError, IndexError):
                    pass
            fonts[(fam, bold, italic)] = data
    _write(path, parts, fonts)
    done = sorted({k[0] for k in fonts})
    return done


def _write(path, parts, fonts):
    """The package with these embedded faces (and no others)."""
    parts = {n: v for n, v in parts.items() if not n.startswith("word/fonts/")}
    ft = parts.get("word/fontTable.xml", b"").decode("utf-8", "replace")
    if not ft:
        ft = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:fonts xmlns:w="%s" '
              'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"></w:fonts>' % W)
    # drop earlier embedding references
    ft = re.sub(r"<w:embed(Regular|Bold|Italic|BoldItalic)\b[^>]*/>", "", ft)
    if "xmlns:r=" not in ft[:600]:
        ft = ft.replace("<w:fonts ", '<w:fonts xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" ', 1)
    rels = []
    by_family = {}
    for k, ((fam, bold, italic), data) in enumerate(sorted(fonts.items())):
        guid = "{%s}" % str(uuid.uuid4()).upper()
        name = "word/fonts/font%d.odttf" % (k + 1)
        parts[name] = obfuscate(data, guid)
        rid = "rIdF%d" % (k + 1)
        rels.append('<Relationship Id="%s" Type="%s" Target="fonts/font%d.odttf"/>' % (rid, REL_FONT, k + 1))
        tag = next(t for t, b, i in FACES if b == bold and i == italic)
        by_family.setdefault(fam, []).append('<w:%s r:id="%s" w:fontKey="%s"/>' % (tag, rid, guid))
    for fam, elems in by_family.items():
        # embed elements come last inside <w:font>, in Regular, Bold, Italic, BoldItalic order
        elems.sort(key=lambda e: [t for t, _b, _i in FACES].index(e[3:e.index(" ")]))
        pat = re.compile(r'(<w:font w:name="%s"[^>]*?)(/>|>(.*?)</w:font>)' % re.escape(_esc(fam)), re.S)
        m = pat.search(ft)
        if m:
            inner = m.group(3) or ""
            ft = ft[:m.start()] + m.group(1) + ">" + inner + "".join(elems) + "</w:font>" + ft[m.end():]
        else:
            ft = ft.replace("</w:fonts>", '<w:font w:name="%s">%s</w:font></w:fonts>' % (_esc(fam), "".join(elems)))
    parts["word/fontTable.xml"] = ft.encode("utf-8")
    rp = "word/_rels/fontTable.xml.rels"
    old = parts.get(rp, b"").decode("utf-8", "replace")
    keep = re.findall(r"<Relationship\b[^>]*/>", old)
    keep = [r for r in keep if REL_FONT not in r]
    if keep or rels:
        parts[rp] = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Relationships xmlns="http://'
                     'schemas.openxmlformats.org/package/2006/relationships">%s</Relationships>'
                     % "".join(keep + rels)).encode("utf-8")
    else:
        parts.pop(rp, None)
    ct = parts["[Content_Types].xml"].decode("utf-8")
    if fonts and 'Extension="odttf"' not in ct:
        ct = ct.replace("<Default ", '<Default Extension="odttf" ContentType="%s"/><Default ' % CT_FONT, 1)
    parts["[Content_Types].xml"] = ct.encode("utf-8")
    # the document must still refer to its font table
    dr = "word/_rels/document.xml.rels"
    if dr in parts and b"fontTable" not in parts[dr]:
        parts[dr] = parts[dr].replace(b"</Relationships>", b'<Relationship Id="rIdFT1" Type="http://schemas.'
                                      b'openxmlformats.org/officeDocument/2006/relationships/fontTable" '
                                      b'Target="fontTable.xml"/></Relationships>')
        if b"fontTable" not in parts["[Content_Types].xml"]:
            parts["[Content_Types].xml"] = parts["[Content_Types].xml"].replace(
                b"</Types>", b'<Override PartName="/word/fontTable.xml" ContentType="application/vnd.openxmlformats-'
                b'officedocument.wordprocessingml.fontTable+xml"/></Types>')
    tmp = path + ".folio-tmp"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as out:
        first = "[Content_Types].xml"
        out.writestr(first, parts.pop(first))
        for n, v in parts.items():
            out.writestr(n, v)
    os.replace(tmp, path)


def _esc(s):
    return s.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")


# ------------------------------------------------------------------ opening
_SESSION_DIR = None


def extract(path):
    """The fonts a .docx carries, written as plain .ttf files where the engine looks for
    fonts this session (FOLIO_FONT_DIRS). Returns the families found."""
    global _SESSION_DIR
    try:
        z = zipfile.ZipFile(path)
    except (OSError, zipfile.BadZipFile):
        return []
    found = []
    with z:
        names = z.namelist()
        if not any(n.startswith("word/fonts/") for n in names) or "word/fontTable.xml" not in names:
            return []
        ft = z.read("word/fontTable.xml").decode("utf-8", "replace")
        rels = z.read("word/_rels/fontTable.xml.rels").decode("utf-8", "replace") \
            if "word/_rels/fontTable.xml.rels" in names else ""
        targets = dict(re.findall(r'Id="([^"]+)"[^>]*Target="([^"]+)"', rels))
        targets.update({a: b for b, a in re.findall(r'Target="([^"]+)"[^>]*Id="([^"]+)"', rels)})
        if _SESSION_DIR is None:
            _SESSION_DIR = tempfile.mkdtemp(prefix="folio-fonts-")
            dirs = [d for d in os.environ.get("FOLIO_FONT_DIRS", "").split(":") if d]
            os.environ["FOLIO_FONT_DIRS"] = ":".join(dirs + [_SESSION_DIR])
        have = {k[0] for k in installed()}
        for m in re.finditer(r'<w:font w:name="([^"]+)"[^>]*>(.*?)</w:font>', ft, re.S):
            fam = m.group(1)
            if fam.lower() in have:
                continue                    # the installed font wins, as in Word
            for e in re.finditer(r'<w:embed(Regular|Bold|Italic|BoldItalic)\b([^>]*)/>', m.group(2)):
                attrs = e.group(2)
                rid = re.search(r'r:id="([^"]+)"', attrs)
                key = re.search(r'w:fontKey="([^"]+)"', attrs)
                if not rid or rid.group(1) not in targets:
                    continue
                part = "word/" + targets[rid.group(1)].lstrip("/").replace("word/", "", 1)
                if part not in names:
                    continue
                data = z.read(part)
                if key:
                    try:
                        data = obfuscate(data, key.group(1))
                    except ValueError:
                        continue
                if data[:4] not in (b"\x00\x01\x00\x00", b"true", b"OTTO"):
                    continue
                out = os.path.join(_SESSION_DIR, "%s-%s.ttf" % (re.sub(r"[^\w]+", "_", fam), e.group(1)))
                with open(out, "wb") as fh:
                    fh.write(data)
                found.append(fam)
    return sorted(set(found))


def cleanup():
    if _SESSION_DIR:
        shutil.rmtree(_SESSION_DIR, ignore_errors=True)
