"""Word 97-2003 (.doc) written by Folio itself (W3-06), from the document model (docxread
reads the .docx the engine saves): a compound file with the WordDocument, 1Table and Data
streams in the binary format Word 97 to 2003 write — text and its formatting, styles, fonts,
lists, sections with headers and footers, tables (nested too), fields and hyperlinks,
footnotes and endnotes, comments, bookmarks and inline pictures."""
import struct
import zlib

from . import docxbuild as B

ICO_RGB = {1: (0, 0, 0), 2: (0, 0, 255), 3: (0, 255, 255), 4: (0, 255, 0), 5: (255, 0, 255),
           6: (255, 0, 0), 7: (255, 255, 0), 8: (255, 255, 255), 9: (0, 0, 128), 10: (0, 128, 128),
           11: (0, 128, 0), 12: (128, 0, 128), 13: (128, 0, 0), 14: (128, 128, 0), 15: (128, 128, 128),
           16: (192, 192, 192)}
HIGHLIGHT = {"black": 1, "blue": 2, "cyan": 3, "green": 4, "magenta": 5, "red": 6, "yellow": 7,
             "white": 8, "darkBlue": 9, "darkCyan": 10, "darkGreen": 11, "darkMagenta": 12,
             "darkRed": 13, "darkYellow": 14, "darkGray": 15, "lightGray": 16}
KUL = {"single": 1, "words": 2, "double": 3, "dotted": 4, "thick": 6, "dash": 7, "dotDash": 9,
       "dotDotDash": 10, "wave": 11, "dottedHeavy": 20, "dashedHeavy": 23, "dashDotHeavy": 25,
       "dashDotDotHeavy": 26, "wavyHeavy": 27, "dashLong": 39, "wavyDouble": 43, "dashLongHeavy": 55}
NFC = {"decimal": 0, "upperRoman": 1, "lowerRoman": 2, "upperLetter": 3, "lowerLetter": 4,
       "ordinal": 5, "cardinalText": 6, "ordinalText": 7, "decimalZero": 22, "bullet": 23, "none": 255}
BRC_TYPE = {"single": 1, "thick": 2, "double": 3, "dotted": 6, "dashed": 7, "dotDash": 8,
            "dotDotDash": 9, "triple": 10, "dashSmallGap": 22, "wave": 20, "doubleWave": 21,
            "thinThickSmallGap": 11, "thickThinSmallGap": 12, "threeDEmboss": 24, "threeDEngrave": 25,
            "inset": 27, "outset": 26}
# Word's built-in style identifiers (sti) for the names it knows
STI = {"Normal": 0, "Heading 1": 1, "Heading 2": 2, "Heading 3": 3, "Heading 4": 4, "Heading 5": 5,
       "Heading 6": 6, "Heading 7": 7, "Heading 8": 8, "Heading 9": 9, "Index 1": 10,
       "TOC 1": 19, "TOC 2": 20, "TOC 3": 21, "TOC 4": 22, "TOC 5": 23, "TOC 6": 24, "TOC 7": 25,
       "TOC 8": 26, "TOC 9": 27, "Footnote Text": 29, "Comment Text": 30, "Annotation Text": 30,
       "Header": 31, "Footer": 32, "Caption": 34, "Table of Figures": 35,
       "Footnote Reference": 38, "Comment Reference": 39, "Endnote Reference": 42,
       "Endnote Text": 43, "List Bullet": 48, "List Number": 49, "Title": 62, "Signature": 64,
       "Default Paragraph Font": 65, "Body Text": 66, "Subtitle": 74, "Hyperlink": 85,
       "FollowedHyperlink": 86, "Strong": 87, "Emphasis": 88, "Plain Text": 90,
       "Normal Table": 105, "No List": 107, "Table Grid": 154, "No Spacing": 157,
       "List Paragraph": 179, "Quote": 180, "Intense Quote": 181, "Subtle Emphasis": 260,
       "Intense Emphasis": 261, "Book Title": 264, "TOC Heading": 266}
FLT = {"HYPERLINK": 88, "PAGE": 33, "NUMPAGES": 26, "DATE": 31, "TIME": 32, "TOC": 13, "REF": 3,
       "PAGEREF": 37, "MERGEFIELD": 59, "SEQ": 12, "AUTHOR": 17, "TITLE": 15, "FILENAME": 29,
       "SECTIONPAGES": 66, "SECTION": 65, "NOTEREF": 72, "STYLEREF": 10, "INCLUDEPICTURE": 67,
       "SYMBOL": 57, "IF": 7, "ASK": 38, "FILLIN": 39, "CREATEDATE": 21, "SAVEDATE": 22,
       "PRINTDATE": 23, "NUMWORDS": 28, "NUMCHARS": 29, "KEYWORDS": 18, "SUBJECT": 16,
       "COMMENTS": 19, "LASTSAVEDBY": 20, "TEMPLATE": 30, "INDEX": 8, "TA": 64, "TOA": 73,
       "XE": 4, "TC": 9, "EQ": 49, "ADDRESSBLOCK": 93, "GREETINGLINE": 94, "MERGEREC": 44,
       "MERGESEQ": 75, "NEXT": 41, "NEXTIF": 42, "SKIPIF": 43, "SET": 6, "DOCPROPERTY": 85,
       "DOCVARIABLE": 64, "QUOTE": 35, "LISTNUM": 90, "BIBLIOGRAPHY": 100, "CITATION": 96}


FSPEC = struct.pack("<HB", 0x0855, 1)


def _rgb(h):
    h = (h or "000000").upper()
    if h == "AUTO" or len(h) != 6:
        return None
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def colorref(h):
    c = _rgb(h)
    if c is None:
        return 0xFF000000
    return c[0] | (c[1] << 8) | (c[2] << 16)


def ico(h):
    c = _rgb(h)
    if c is None:
        return 0
    best, bd = 1, 1e9
    for k, v in ICO_RGB.items():
        d = sum((a - b) ** 2 for a, b in zip(c, v))
        if d < bd:
            best, bd = k, d
    return best


def sp(op, data):
    return struct.pack("<H", op) + data


def sp1(op, v):
    return struct.pack("<HB", op, v & 0xFF)


def sp2(op, v):
    return struct.pack("<Hh" if v < 0 else "<HH", op, v)


def sp4(op, v):
    return struct.pack("<HI", op, v & 0xFFFFFFFF)


def spv(op, data):
    """A sprm with a variable operand: one length byte, then the data."""
    return struct.pack("<HB", op, len(data)) + data


def brc80(b):
    if not b or b[2] in ("nil", "none"):
        return b"\x00\x00\x00\x00" if not b or b[2] == "nil" else b"\xff\xff\xff\xff"[:0] + b"\x00" * 4
    sz, color, kind, space = (list(b) + [None] * 4)[:4]
    return struct.pack("<BBBB", min(255, max(1, sz or 4)), BRC_TYPE.get(kind or "single", 1),
                       ico(color) if color and color != "auto" else 0, min(31, space or 0))


def brc(b):
    if not b or b[2] in ("nil", "none"):
        return b"\x00" * 8
    sz, color, kind, space = (list(b) + [None] * 4)[:4]
    return struct.pack("<IBBBB", colorref(color) if color and color != "auto" else 0xFF000000,
                       min(255, max(1, sz or 4)), BRC_TYPE.get(kind or "single", 1),
                       min(31, space or 0), 0)


def shd_operand(back):
    return struct.pack("<IIH", 0xFF000000, colorref(back), 0)


class Story:
    """One of the document's stories being written: its characters, the formatting of each
    run of them and the paragraphs they make."""

    def __init__(self):
        self.chars = []         # str pieces
        self.n = 0
        self.runs = []          # (cp0, cp1, chpx)
        self.paras = []         # (cp end after the mark, istd, papx)
        self.fields = []        # (cp, kind 0x13/0x14/0x15, flt or flags)
        self.bkf = []           # (cp, name)
        self.bkl = []           # (cp, name)
        self.notes = []         # (cp, kind, blocks)
        self.comments = []      # (cp, comment)
        self.cstarts = {}       # comment id: cp where its range starts
        self.main = False
        self.pics = []          # (cp, run)

    def add(self, text, chpx=b""):
        if not text:
            return
        cp = self.n
        self.chars.append(text)
        self.n += len(text.encode("utf-16-le")) // 2   # character positions count UTF-16 units
        if self.runs and self.runs[-1][2] == chpx and self.runs[-1][1] == cp:
            a = self.runs[-1]
            self.runs[-1] = (a[0], self.n, chpx)
        else:
            self.runs.append((cp, self.n, chpx))

    def end_para(self, mark, istd, papx, mark_chpx=b""):
        self.add(mark, mark_chpx)
        self.paras.append((self.n, istd, papx))

    def text(self):
        return "".join(self.chars)


class Writer:
    def __init__(self, doc):
        self.doc = doc
        self.fonts = []
        self.data = bytearray()
        self.istd = {}
        self.lfo_of = {}
        self.bm_names = []

    # ------------------------------------------------------------------ fonts
    def font(self, name):
        name = name or "Times New Roman"
        if name not in self.fonts:
            self.fonts.append(name)
        return self.fonts.index(name)

    def sttbf_ffn(self):
        out = [struct.pack("<HH", len(self.fonts), 0)]
        for name in self.fonts:
            ff = 2 if name.lower() in ("times new roman", "georgia", "cambria", "garamond") else 0
            body = struct.pack("<BhBB", 0x04 | (ff << 4) | 0x02, 400, 0, 0) + b"\x00" * 10 + b"\x00" * 24
            body += (name + "\x00").encode("utf-16-le")
            out.append(struct.pack("<B", len(body)) + body)
        return b"".join(out)

    # -------------------------------------------------------------- properties
    def chpx(self, r, cstyle=None):
        out = []
        if cstyle and cstyle in self.istd:
            out.append(sp2(0x4A30, self.istd[cstyle]))
        for k, op in (("b", 0x0835), ("i", 0x0836), ("strike", 0x0837), ("outline", 0x0838),
                      ("shadow", 0x0839), ("smallcaps", 0x083A), ("caps", 0x083B), ("hidden", 0x083C),
                      ("imprint", 0x0854), ("emboss", 0x0858)):
            if k in r:
                out.append(sp1(op, 1 if r[k] else 0))
                if k in ("b", "i"):
                    out.append(sp1(0x085C if k == "b" else 0x085D, 1 if r[k] else 0))
        if r.get("dstrike"):
            out.append(sp1(0x2A53, 1))
        if "u" in r:
            u = r["u"]
            out.append(sp1(0x2A3E, KUL.get(u, 1) if u and u != "none" else 0))
        if r.get("color"):
            out.append(sp1(0x2A42, ico(r["color"])))
            out.append(sp4(0x6870, colorref(r["color"])))
        if r.get("sz"):
            out.append(sp2(0x4A43, r["sz"]))
            out.append(sp2(0x4A61, r["sz"]))
        if r.get("font"):
            f = self.font(r["font"])
            out.append(sp2(0x4A4F, f))
            out.append(sp2(0x4A51, f))
        if r.get("font_ea"):
            out.append(sp2(0x4A50, self.font(r["font_ea"])))
        if r.get("font_cs"):
            out.append(sp2(0x4A5E, self.font(r["font_cs"])))
        if r.get("vert") in ("superscript", "subscript"):
            out.append(sp1(0x2A48, 1 if r["vert"] == "superscript" else 2))
        if r.get("highlight") in HIGHLIGHT:
            out.append(sp1(0x2A0C, HIGHLIGHT[r["highlight"]]))
        if r.get("spacing"):
            out.append(sp2(0x8840, r["spacing"]))
        if r.get("scale") and r["scale"] != 100:
            out.append(sp2(0x4852, r["scale"]))
        if r.get("position"):
            out.append(sp2(0x4845, r["position"]))
        if r.get("shd"):
            out.append(spv(0xCA71, shd_operand(r["shd"])))
        return b"".join(out)

    def papx(self, p):
        out = []
        al = p.get("align")
        if al:
            jc = {"left": 0, "start": 0, "center": 1, "right": 2, "end": 2, "both": 3, "distribute": 4}.get(al, 0)
            out.append(sp1(0x2403, jc))
            out.append(sp1(0x2461, jc))
        if p.get("keep_lines"):
            out.append(sp1(0x2405, 1))
        if p.get("keep_next"):
            out.append(sp1(0x2406, 1))
        if p.get("pbb"):
            out.append(sp1(0x2407, 1))
        if "widow" in p:
            out.append(sp1(0x2431, 1 if p["widow"] else 0))
        if "ind_r" in p:
            out.append(sp2(0x840E, p["ind_r"]))
            out.append(sp2(0x845D, p["ind_r"]))
        if "ind_l" in p:
            out.append(sp2(0x840F, p["ind_l"]))
            out.append(sp2(0x845E, p["ind_l"]))
        if "ind_first" in p:
            out.append(sp2(0x8411, p["ind_first"]))
            out.append(sp2(0x8460, p["ind_first"]))
        if "sb" in p:
            out.append(sp2(0xA413, p["sb"]))
        if "sa" in p:
            out.append(sp2(0xA414, p["sa"]))
        if "line" in p:
            rule = p.get("line_rule", "auto")
            if rule == "auto":
                out.append(struct.pack("<Hhh", 0x6412, p["line"], 1))
            elif rule == "exact":
                out.append(struct.pack("<Hhh", 0x6412, -p["line"], 0))
            else:
                out.append(struct.pack("<Hhh", 0x6412, p["line"], 0))
        if p.get("outline") is not None:
            out.append(sp1(0x2640, p["outline"]))
        if p.get("bidi"):
            out.append(sp1(0x2441, 1))
        if p.get("contextual"):
            out.append(sp1(0x246D, 1))
        if p.get("num") is not None:
            n, lvl = p["num"]
            if n >= 0 and n in self.lfo_of:
                out.append(sp2(0x460B, self.lfo_of[n]))
                out.append(sp1(0x260A, lvl))
            elif n < 0:
                out.append(sp2(0x460B, 0))
        tabs = p.get("tabs") or []
        if tabs:
            add = [(pos, kind, lead) for pos, kind, lead in tabs][:64]
            data = struct.pack("<BB", 0, len(add))
            data += b"".join(struct.pack("<h", t[0]) for t in add)
            data += bytes(({"left": 0, "center": 1, "right": 2, "decimal": 3, "bar": 4}.get(t[1], 0) |
                           ({"dot": 1, "hyphen": 2, "underscore": 3, "heavy": 4, "middleDot": 5}.get(t[2], 0) << 3))
                          for t in add)
            out.append(spv(0xC60D, data))
        for side, op80, op in (("top", 0x6424, 0xC64E), ("left", 0x6425, 0xC64F),
                               ("bottom", 0x6426, 0xC650), ("right", 0x6427, 0xC651),
                               ("between", 0x6428, 0xC652)):
            b = (p.get("borders") or {}).get(side)
            if b and b[2] not in ("nil", "none"):
                out.append(struct.pack("<H", op80) + brc80(b))
                out.append(spv(op, brc(b)))
        if p.get("shd"):
            out.append(spv(0xC64D, shd_operand(p["shd"])))
        return b"".join(out)

    # ------------------------------------------------------------------ styles
    def plan_styles(self):
        d = self.doc
        fixed = {"Normal": 0, "Heading1": 1, "Heading2": 2, "Heading3": 3, "Heading4": 4,
                 "Heading5": 5, "Heading6": 6, "Heading7": 7, "Heading8": 8, "Heading9": 9,
                 "DefaultParagraphFont": 10, "TableNormal": 11, "NoList": 12}
        nxt = 15
        for st in d.styles:
            sid = st["id"]
            if st.get("default") and st["type"] == "paragraph":
                self.istd[sid] = 0
            elif sid in fixed and sid not in self.istd and fixed[sid] not in self.istd.values():
                self.istd[sid] = fixed[sid]
            else:
                self.istd[sid] = nxt
                nxt += 1
        if 0 not in self.istd.values():
            self.istd["Normal"] = 0
        for sid, n in (("DefaultParagraphFont", 10), ("TableNormal", 11), ("NoList", 12)):
            if sid not in self.istd and n not in self.istd.values():
                self.istd[sid] = n
        self.istd_max = max(self.istd.values()) + 1

    def stsh(self):
        d = self.doc
        by_istd = {}
        for st in d.styles:
            by_istd[self.istd[st["id"]]] = st
        dr = d.defaults.get("rpr", {})
        f0 = self.font(dr.get("font") or "Times New Roman")
        cstd = max(self.istd_max, 15)
        stshi = struct.pack("<HHHHHH", cstd, 10, 1, 0x05B2, 15, 0) + struct.pack("<HHH", f0, f0, f0)
        out = [struct.pack("<H", len(stshi)), stshi]
        for istd in range(cstd):
            st = by_istd.get(istd)
            if st is None:
                if istd == 10:
                    st = {"id": "DefaultParagraphFont", "name": "Default Paragraph Font",
                          "type": "character", "ppr": {}, "rpr": {}}
                elif istd == 11:
                    st = {"id": "TableNormal", "name": "Normal Table", "type": "table", "ppr": {}, "rpr": {}}
                elif istd == 12:
                    st = {"id": "NoList", "name": "No List", "type": "numbering", "ppr": {}, "rpr": {}}
                else:
                    out.append(struct.pack("<H", 0))
                    continue
            out.append(self.std(istd, st, by_istd))
        return b"".join(out)

    def std(self, istd, st, by_istd):
        kind = st["type"]
        stk = {"paragraph": 1, "character": 2, "table": 3, "numbering": 4}.get(kind, 1)
        name = st.get("name") or st["id"]
        sti = STI.get(name, 0x0FFE)
        if istd == 0:
            sti = 0
        base = self.istd.get(st.get("based"), 0x0FFF) if st.get("based") else 0x0FFF
        if kind == "character" and istd != 10 and base == 0x0FFF:
            base = 10
        nxt = self.istd.get(st.get("next"), istd) if kind == "paragraph" else istd
        if kind == "paragraph":
            ppr, rpr = st.get("ppr") or {}, st.get("rpr") or {}
            if base == 0x0FFF:
                # a .doc has no document defaults: styles at the root carry them
                ppr = dict(self.doc.defaults.get("ppr") or {}, **ppr)
                rpr = dict(self.doc.defaults.get("rpr") or {}, **rpr)
            upx = [struct.pack("<H", istd) + self.papx(ppr), self.chpx(rpr)]
        elif kind == "character":
            upx = [self.chpx(st.get("rpr") or {})]
        elif kind == "table":
            upx = [b"", struct.pack("<H", istd), b""]
        else:
            upx = [b""]
        # pad names and upxs as Word does
        xstz = struct.pack("<H", len(name)) + name.encode("utf-16-le") + b"\x00\x00"
        body = bytearray(xstz)
        for u in upx:
            if len(body) % 2:
                body += b"\x00"
            body += struct.pack("<H", len(u)) + u
            if len(u) % 2:
                body += b"\x00"
        base_hdr = struct.pack("<HHHHH", sti & 0x0FFF, stk | (base << 4), len(upx) | (nxt << 4),
                               10 + len(body), 0)
        std = base_hdr + bytes(body)
        return struct.pack("<H", len(std)) + std

    # ------------------------------------------------------------------- lists
    def lists(self):
        d = self.doc
        if not d.nums:
            return b"", b""
        # one list per instance: list instances that restart get their own list
        lstf = []
        lvls = []
        lfo = []
        lfodata = []
        for ni, (ai, restart) in enumerate(d.nums):
            levels = d.lists[ai][:9] if ai < len(d.lists) else []
            while len(levels) < 9:
                i = len(levels)
                levels = list(levels) + [{"fmt": "decimal", "text": "%%%d." % (i + 1), "ind": 720 * (i + 1), "hang": 360}]
            lsid = 0x10000000 + ni
            lstf.append(struct.pack("<ii", lsid, lsid + 0x01000000) + struct.pack("<9H", *([0x0FFF] * 9)) +
                        struct.pack("<BB", 0, 0))
            for li, lv in enumerate(levels):
                lvls.append(self.lvl(li, lv))
            lfo.append(struct.pack("<iiiBBBB", lsid, 0, 0, 0, 0, 0, 0))
            lfodata.append(struct.pack("<I", 0xFFFFFFFF))
            self.lfo_of[ni] = ni + 1
        plflst = (struct.pack("<H", len(lstf)) + b"".join(lstf), b"".join(lvls))
        plflfo = struct.pack("<I", len(lfo)) + b"".join(lfo) + b"".join(lfodata)
        return plflst, plflfo

    def lvl(self, li, lv):
        fmt = lv.get("fmt", "decimal")
        text = lv.get("text")
        if text is None:
            text = lv.get("bullet", "•") if fmt == "bullet" else "%%%d." % (li + 1)
        xst = []
        nums = []
        k = 0
        while k < len(text):
            if text[k] == "%" and k + 1 < len(text) and text[k + 1].isdigit():
                xst.append(chr(int(text[k + 1]) - 1))
                nums.append(len(xst))
                k += 2
                continue
            xst.append(text[k])
            k += 1
        nums = (nums + [0] * 9)[:9]
        ind = lv.get("ind", 720 * (li + 1))
        hang = lv.get("hang", 360)
        papx = sp2(0x840F, ind) + sp2(0x845E, ind) + sp2(0x8411, -hang) + sp2(0x8460, -hang)
        chpx = b""
        if lv.get("font"):
            f = self.font(lv["font"])
            chpx = sp2(0x4A4F, f) + sp2(0x4A51, f)
        jc = {"left": 0, "center": 1, "right": 2}.get(lv.get("jc", "left"), 0)
        start = lv.get("start", 1)
        lvlf = struct.pack("<iBB9BBiIBBBB", start, NFC.get(fmt, 0), jc, *nums, 0, 0, 0,
                           len(chpx), len(papx), 0, 0)
        s = "".join(xst)
        return lvlf + papx + chpx + struct.pack("<H", len(s)) + s.encode("utf-16-le")

    # ------------------------------------------------------------------ stories
    def story(self, blocks, st, kind="main", sect_marks=None):
        """Write blocks into a story; sect_marks: indexes of blocks that end a section."""
        for i, b in enumerate(blocks):
            last_in_sect = sect_marks is not None and i in sect_marks
            if b.get("table"):
                self.table(b, st, 1)
                if last_in_sect:
                    st.end_para("\x0c", 0, b"")
            else:
                self.para(b, st, mark="\x0c" if last_in_sect else "\r")

    def para(self, b, st, mark="\r", depth=0, cell_end=False, row_end_papx=None):
        istd = self.istd.get(b.get("style"), 0) if b.get("style") else 0
        self.runs(b.get("runs", []), st)
        px = self.papx(b.get("ppr") or {})
        if depth:
            px += sp1(0x2416, 1) + struct.pack("<HI", 0x6649, depth)
            if cell_end and depth > 1:
                px += sp1(0x244B, 1)
        mk = self.chpx(b.get("rpr") or {})
        if cell_end and depth == 1:
            mark = "\x07"
        st.end_para(mark, istd, px, mk)

    def runs(self, runs, st, base=None):
        for r in runs:
            t = r.get("t")
            cx = self.chpx(r.get("rpr") or {}, r.get("cstyle"))
            if t == "text":
                txt = r.get("text", "").replace("\n", "\x0b").replace("\r", "\x0b")
                txt = "".join(c for c in txt if c in "\t\x0b" or ord(c) >= 32)
                st.add(txt, cx)
            elif t == "tab":
                st.add("\t", cx)
            elif t == "br":
                st.add("\x0b", cx)
            elif t == "page":
                st.add("\x0c", cx)
            elif t == "col":
                st.add("\x0e", cx)
            elif t == "image":
                fc = self.picture(r)
                if fc is not None:
                    st.pics.append((st.n, r))
                    st.add("\x01", cx + sp1(0x0855, 1) + sp4(0x6A03, fc))
            elif t == "note":
                st.notes.append((st.n, r.get("kind", "footnote"), r.get("blocks") or [B.para()]))
                st.add("\x02", cx + sp1(0x0855, 1))
            elif t == "field":
                res = r.get("result", "")
                self.field(st, r.get("instr", ""), (lambda res=res, cx=cx: self.runs(res, st) if isinstance(res, list)
                                                    else st.add(str(res or ""), cx)), cx)
            elif t == "fbegin":
                instr = r.get("instr", "")
                st.fields.append((st.n, 0x13, FLT.get((instr.split() or [""])[0].upper(), 0)))
                st.add("\x13", cx + FSPEC)
                st.add(" %s " % instr, cx)
            elif t == "fsep":
                st.fields.append((st.n, 0x14, 0))
                st.add("\x14", cx + FSPEC)
            elif t == "fend":
                st.fields.append((st.n, 0x15, 0x80))
                st.add("\x15", cx + FSPEC)
            elif t == "link":
                url = r.get("url") or ""
                anchor = r.get("anchor")
                if "#" in url:
                    url, anchor = url.split("#", 1)
                instr = 'HYPERLINK "%s"' % url if url else ""
                if anchor:
                    instr = (instr + ' \\l "%s"' % anchor) if instr else 'HYPERLINK \\l "%s"' % anchor
                inner = r.get("runs", [])
                if instr:
                    self.field(st, instr, lambda inner=inner: self.runs(inner, st), cx)
                else:
                    self.runs(inner, st)
            elif t == "bmstart":
                st.bkf.append((st.n, r["name"]))
            elif t == "bmend":
                st.bkl.append((st.n, r["name"]))
            elif t == "cstart":
                st.cstarts.setdefault(r.get("id"), st.n)
            elif t == "cend":
                c = next((c for c in self.doc.comments if c.get("id") == r.get("id")), None)
                if c is not None and st.main:   # Word keeps comments in the main text only
                    st.comments.append((st.n, c))
                    st.add("\x05", cx + sp1(0x0855, 1))

    def field(self, st, instr, result_fn, cx):
        name = (instr.split() or [""])[0].upper()
        st.fields.append((st.n, 0x13, FLT.get(name, 0)))
        st.add("\x13", cx + FSPEC)
        st.add(" %s " % instr.strip(), cx)
        st.fields.append((st.n, 0x14, 0))
        st.add("\x14", cx + FSPEC)
        result_fn()
        st.fields.append((st.n, 0x15, 0x80))
        st.add("\x15", cx + FSPEC)

    def table(self, t, st, depth):
        cols = t.get("cols") or []
        ncol = max((sum(c.get("span", 1) for c in r["cells"]) for r in t["rows"]), default=1)
        if not cols:
            cols = [9360 // max(1, ncol)] * ncol
        has_cell_borders = any(c.get("borders") for r in t["rows"] for c in r["cells"])
        default_borders = t.get("borders", True) and not t.get("style") and not has_cell_borders
        left = t.get("indent", 0)
        for row in t["rows"]:
            cells = row.get("cells") or []
            if not cells:
                continue
            for c in cells:
                blocks = c.get("blocks") or [B.para()]
                for i, b in enumerate(blocks):
                    last = i == len(blocks) - 1
                    if b.get("table"):
                        self.table(b, st, depth + 1)
                        if last:
                            self.para(B.para(), st, depth=depth, cell_end=True)
                    else:
                        self.para(b, st, depth=depth, cell_end=last)
            # the row's end: its table properties
            tap = self.tap(t, row, cols, left, default_borders)
            px = sp1(0x2416, 1) + struct.pack("<HI", 0x6649, depth) + tap
            if depth == 1:
                px += sp1(0x2417, 1)
                st.end_para("\x07", 0, px)
            else:
                px += sp1(0x244B, 1) + sp1(0x244C, 1)
                st.end_para("\r", 0, px)

    def tap(self, t, row, cols, left, default_borders):
        cells = row["cells"]
        x = left - 108
        centers = [x]
        tcs = []
        shds = []
        ci = 0
        for c in cells:
            span = c.get("span", 1)
            w = sum(cols[ci:ci + span]) if ci + span <= len(cols) else (c.get("width") or 2160)
            ci += span
            x += w
            centers.append(x)
            rgf = 0
            if c.get("vmerge") == "restart":
                rgf |= 0x0060
            elif c.get("vmerge") == "cont":
                rgf |= 0x0020
            va = {"top": 0, "center": 1, "bottom": 2}.get(c.get("valign"), 0)
            rgf |= va << 7
            bd = c.get("borders") or {}
            brs = []
            for side in ("top", "left", "bottom", "right"):
                if side in bd:
                    brs.append(brc80(bd[side]))
                elif default_borders:
                    brs.append(struct.pack("<BBBB", 4, 1, 0, 0))
                else:
                    brs.append(b"\x00\x00\x00\x00")
            tcs.append(struct.pack("<HH", rgf, 0) + b"".join(brs))
            shds.append(shd_operand(c["shd"]) if c.get("shd") else struct.pack("<IIH", 0xFF000000, 0xFF000000, 0))
        itc = len(cells)
        body = struct.pack("<B", itc) + b"".join(struct.pack("<h", v) for v in centers) + b"".join(tcs)
        out = [struct.pack("<HH", 0xD608, len(body) + 1) + body]
        out.append(sp2(0x9602, 108))
        out.append(sp2(0x9601, left - 108 if left else -108))
        if t.get("align") in ("center", "right"):
            jc = {"center": 1, "right": 2}[t["align"]]
            out.append(sp2(0x5400, jc))
        if row.get("height"):
            out.append(sp2(0x9407, -row["height"] if row.get("exact") else row["height"]))
        if row.get("header"):
            out.append(sp1(0x3404, 1))
        if row.get("cant_split"):
            out.append(sp1(0x3403, 1))
        if any(c.get("shd") for c in cells):
            data = b"".join(shds)
            out.append(spv(0xD612, data))
        if default_borders:
            out.append(spv(0xD605, struct.pack("<BBBB", 4, 1, 0, 0) * 6))
        return b"".join(out)

    # ----------------------------------------------------------------- pictures
    def picture(self, r):
        ext = (r.get("ext") or "png").lower()
        data = r.get("data") or b""
        if not data:
            return None
        rt = {"png": (0xF01E, 0x6E0), "jpg": (0xF01D, 0x46A), "jpeg": (0xF01D, 0x46A),
              "emf": (0xF01A, 0x3D4), "wmf": (0xF01B, 0x216), "bmp": (0xF01F, 0x7A8)}.get(ext)
        if rt is None:
            data = _as_png(data)
            if data is None:
                return None
            ext, rt = "png", (0xF01E, 0x6E0)
        if ext == "bmp" and data[:2] == b"BM":
            data = data[14:]
        uid = zlib.crc32(data).to_bytes(4, "little") * 4
        if rt[0] in (0xF01A, 0xF01B):
            # metafiles: a compressed header record
            comp = zlib.compress(data)
            meta = struct.pack("<I", len(data)) + struct.pack("<iiii", 0, 0, 0, 0) + struct.pack("<ii", 0, 0) + \
                struct.pack("<I", len(comp)) + b"\x00\xfe"
            blip_body = uid + meta + comp
        else:
            blip_body = uid + b"\xff" + data
        blip = struct.pack("<HHI", rt[1] << 4, rt[0], len(blip_body)) + blip_body
        btw = {0xF01E: 6, 0xF01D: 5, 0xF01A: 2, 0xF01B: 3, 0xF01F: 7}[rt[0]]
        fbse_body = struct.pack("<BB", btw, btw) + uid + struct.pack("<HIIIBBBB", 0xFF, len(blip), 1, 0, 0, 0, 0, 0)
        fbse = struct.pack("<HHI", 0x0002 | (btw << 4), 0xF007, len(fbse_body) + len(blip)) + fbse_body + blip
        cx = int(r.get("cx", 914400) / B.EMU_PER_TWIP)
        cy = int(r.get("cy", 914400) / B.EMU_PER_TWIP)
        # the inline shape: a picture frame showing blip 1 (the one that follows)
        fsp = struct.pack("<HHI", 0x0002 | (75 << 4), 0xF00A, 8) + struct.pack("<II", 1025 + len(self.data) % 10000, 0x0A00)
        opt_props = struct.pack("<HI", 0x4104, 1) + struct.pack("<HI", 0x0105, 0)
        fopt = struct.pack("<HHI", 0x0003 | (2 << 4), 0xF00B, len(opt_props)) + opt_props
        spc_body = fsp + fopt
        spc = struct.pack("<HHI", 0x000F, 0xF004, len(spc_body)) + spc_body
        tail = spc + fbse
        picf = struct.pack("<IHHhhH", 68 + len(tail), 68, 0x64, 0, 0, 0)
        picf += b"\x00" * 14
        picf += struct.pack("<hhHH", min(cx, 32767), min(cy, 32767), 1000, 1000)
        picf += struct.pack("<hhhh", 0, 0, 0, 0)
        picf += b"\x00" * 16 + struct.pack("<hhH", 0, 0, 0)
        picf = picf[:68].ljust(68, b"\x00")
        fc = len(self.data)
        self.data += picf + tail
        return fc

    # ------------------------------------------------------------------ the file
    def write(self):
        d = self.doc
        self.plan_styles()
        plflst, plflfo = self.lists()
        main = Story()
        main.main = True
        secs = d.sections or [B.section()]
        sect_ends = []
        for si, s in enumerate(secs):
            blocks = s["blocks"] or [B.para()]
            marks = {len(blocks) - 1} if si < len(secs) - 1 else set()
            self.story(blocks, main, sect_marks=marks)
            sect_ends.append(main.n)
        # notes and comments found in the main text (and in each other)
        ftn, edn, atn = Story(), Story(), Story()
        ftn_refs, edn_refs, atn_refs = [], [], []
        ftn_txt, edn_txt, atn_txt = [], [], []
        hdd = Story()

        def drain(src):
            for cp, kind, blocks in src.notes:
                tgt, refs, txt = (edn, edn_refs, edn_txt) if kind == "endnote" else (ftn, ftn_refs, ftn_txt)
                refs.append((cp, src))
                txt.append(tgt.n)
                tgt.add("\x02", sp1(0x0855, 1) + sp1(0x2A48, 1))
                self.story(blocks, tgt)
            src.notes = []
            for cp, c in src.comments:
                atn_refs.append((cp, c))
                atn_txt.append(atn.n)
                atn.add("\x05", sp1(0x0855, 1))
                self.story(c.get("blocks") or [B.para()], atn)
            src.comments = []
        # headers and footers: six separator stories, then six per section
        hdd_cps = []
        for _k in range(6):
            hdd_cps.append(hdd.n)
        order = [("headers", "even"), ("headers", "default"), ("footers", "even"), ("footers", "default"),
                 ("headers", "first"), ("footers", "first")]
        for s in secs:
            for key, typ in order:
                hdd_cps.append(hdd.n)
                hf = s.get(key) or {}
                blocks = hf.get(typ) or (hf.get("odd") if typ == "default" else None)
                if blocks:
                    self.story(blocks, hdd)
        drain(main)
        drain(hdd)
        drain(ftn)
        drain(edn)
        # a story's end: one more paragraph mark after the last
        hdd_cps.append(hdd.n)
        for story in (ftn, edn, atn, hdd):
            if story.n:
                story.end_para("\r", 0, b"")
        hdd_cps.append(hdd.n)
        stories = [main, ftn, hdd, atn, edn]
        ccp = {"text": main.n, "ftn": ftn.n, "hdd": hdd.n, "atn": atn.n, "edn": edn.n}
        any_sub = ftn.n or hdd.n or atn.n or edn.n
        tail = Story()
        if any_sub:
            tail.end_para("\r", 0, b"")
        text = "".join(s.text() for s in stories) + tail.text()
        base = {"text": 0, "ftn": main.n, "hdd": main.n + ftn.n, "atn": main.n + ftn.n + hdd.n,
                "edn": main.n + ftn.n + hdd.n + atn.n}
        total = len(text.encode("utf-16-le")) // 2
        # ---- WordDocument: FIB, text, sections' sprms, FKPs
        fc_text = 0x800
        wd = bytearray(fc_text)
        wd += text.encode("utf-16-le")
        # the formatting of every character, in story order
        runs, paras = [], []
        for s, key in ((main, "text"), (ftn, "ftn"), (hdd, "hdd"), (atn, "atn"), (edn, "edn"), (tail, None)):
            b0 = base[key] if key else main.n + ftn.n + hdd.n + atn.n + edn.n
            for a, z, cx in s.runs:
                runs.append((b0 + a, b0 + z, cx))
            for z, istd, px in s.paras:
                paras.append((b0 + z, istd, px))
        # every character in exactly one run and one paragraph
        runs = _cover(runs, total, b"")
        fcp = lambda cp: fc_text + 2 * cp  # noqa: E731
        # SEPX for each section
        sepx_fc = []
        for s in secs:
            while len(wd) % 2:
                wd += b"\x00"
            g = self.sepx(s)
            sepx_fc.append(len(wd))
            wd += struct.pack("<h", len(g)) + g
        # FKPs
        while len(wd) % 512:
            wd += b"\x00"
        chp_bte = []
        for page, fc0, fc1 in _chpx_fkps([(fcp(a), fcp(z), cx) for a, z, cx in runs]):
            chp_bte.append((fc0, fc1, len(wd) // 512))
            wd += page
        pap_bte = []
        prs = []
        prev = 0
        for z, istd, px in sorted(paras):
            if z > prev:
                prs.append((fcp(prev), fcp(z), istd, px))
                prev = z
        if prev < total:
            prs.append((fcp(prev), fcp(total), 0, b""))
        for page, fc0, fc1 in _papx_fkps(prs):
            pap_bte.append((fc0, fc1, len(wd) // 512))
            wd += page
        # ---- 1Table
        tb = bytearray()
        fclcb = [(0, 0)] * 93

        def put(idx, data):
            if not data:
                return
            while len(tb) % 2:
                tb.append(0)
            fclcb[idx] = (len(tb), len(data))
            tb.extend(data)
        stsh = self.stsh()
        put(1, stsh)
        fclcb[0] = fclcb[1]
        put(2, self.plc([b0 for b0, _s in [(cp, s) for cp, s in ftn_refs]], [ftn_refs and ftn.n], 2, ftn_refs, "ref"))
        put(3, self.plc_cps(ftn_txt, ftn.n))
        put(46, self.plc([cp for cp, _s in edn_refs], None, 2, edn_refs, "ref"))
        put(47, self.plc_cps(edn_txt, edn.n))
        put(4, self.atrd(atn_refs, main))
        rng = self.atn_ranges(atn_refs, main)
        if rng:
            put(37, rng[0])
            put(42, rng[1])
            put(43, rng[2])
        put(5, self.plc_cps(atn_txt, atn.n))
        put(36, self.owners(atn_refs))
        # sections
        sed_cps = [0] + sect_ends
        sed = b"".join(struct.pack("<I", c) for c in sed_cps)
        sed += b"".join(struct.pack("<hIhI", 0, fc, 0, 0xFFFFFFFF) for fc in sepx_fc)
        put(6, sed)
        put(11, b"".join(struct.pack("<I", c) for c in hdd_cps) if hdd.n else b"")
        put(12, _plc_bte(chp_bte))
        put(13, _plc_bte(pap_bte))
        put(15, self.sttbf_ffn())
        put(16, _plcfld(main.fields, 0, main.n))
        put(17, _plcfld(hdd.fields, 0, hdd.n))
        put(18, _plcfld(ftn.fields, 0, ftn.n))
        put(19, _plcfld(atn.fields, 0, atn.n))
        put(48, _plcfld(edn.fields, 0, edn.n))
        bk = self.bookmarks(main)
        if bk:
            put(21, bk[0])
            put(22, bk[1])
            put(23, bk[2])
        put(31, self.dop())
        clx = struct.pack("<BI", 2, 16) + struct.pack("<II", 0, total) + struct.pack("<HIH", 0, fc_text, 0)
        put(33, clx)
        if plflst:
            # the LVLs follow PlfLst in the table stream, outside its count
            put(73, plflst[0])
            tb.extend(plflst[1])
            put(74, plflfo)
        # ---- FIB
        fib = self.fib(fclcb, ccp, len(wd), fc_text, fc_text + 2 * total,
                       ((chp_bte[0][2] if chp_bte else 0, len(chp_bte)),
                        (pap_bte[0][2] if pap_bte else 0, len(pap_bte))))
        wd[0:len(fib)] = fib
        streams = {"WordDocument": bytes(wd), "1Table": bytes(tb)}
        if self.data:
            streams["Data"] = bytes(self.data)
        streams["\x05SummaryInformation"] = _summary(d.meta or {})
        return cfb(streams)

    def sepx(self, s):
        out = []
        brk = {"continuous": 0, "nextColumn": 1, "nextPage": 2, "evenPage": 3, "oddPage": 4}.get(s.get("break"), 2)
        out.append(sp1(0x3009, brk))
        if s.get("title_pg"):
            out.append(sp1(0x300A, 1))
        if s.get("cols", 1) > 1:
            out.append(sp2(0x500B, s["cols"] - 1))
            out.append(sp2(0x900C, s.get("col_space", 720)))
        m = s["margins"]
        out.append(sp2(0xB017, m.get("header", 720)))
        out.append(sp2(0xB018, m.get("footer", 720)))
        if s.get("page_start"):
            out.append(sp1(0x3011, 1))
            out.append(sp2(0x501C, s["page_start"]))
        if s.get("landscape"):
            out.append(sp1(0x301D, 2))
        out.append(sp2(0xB01F, s["w"]))
        out.append(sp2(0xB020, s["h"]))
        out.append(sp2(0xB021, m["left"]))
        out.append(sp2(0xB022, m["right"]))
        out.append(sp2(0x9023, m["top"]))
        out.append(sp2(0x9024, m["bottom"]))
        out.append(sp2(0xB025, m.get("gutter", 0)))
        return b"".join(out)

    def plc(self, cps, _unused, cbdata, refs, kind):
        if not refs:
            return b""
        cps = [cp for cp, _s in refs]
        data = b"".join(struct.pack("<h", 1) for _ in refs)   # FRD: numbered automatically
        last = cps[-1] + 1
        return b"".join(struct.pack("<I", c) for c in cps + [last]) + data

    def plc_cps(self, starts, end):
        if not starts:
            return b""
        cps = list(starts) + [end - 1, end]
        return b"".join(struct.pack("<I", c) for c in cps)

    def owners(self, refs):
        names = []
        for _cp, c in refs:
            a = c.get("author") or "Author"
            if a not in names:
                names.append(a)
        self._owners = names
        return b"".join(struct.pack("<H", len(n)) + n.encode("utf-16-le") for n in names)

    def atn_ranges(self, refs, main):
        """The commented ranges: SttbfAtnBkmk, PlcfAtnBkf, PlcfAtnBkl."""
        rs = []
        for k, (cp, c) in enumerate(refs):
            a = main.cstarts.get(c.get("id"))
            if a is not None and a <= cp:
                rs.append((a, cp, k))
        if not rs:
            return None
        by_start = sorted(range(len(rs)), key=lambda i: (rs[i][0], i))
        by_end = sorted(range(len(rs)), key=lambda i: (rs[i][1], i))
        ibkl = {i: n for n, i in enumerate(by_end)}
        sttb = struct.pack("<HHH", 0xFFFF, len(rs), 10) + b"".join(
            struct.pack("<H", 0) + struct.pack("<Hii", 0x0100, n, -1) for n in range(len(by_start)))
        last = main.n + 1
        bkf = b"".join(struct.pack("<I", rs[i][0]) for i in by_start) + struct.pack("<I", last)
        bkf += b"".join(struct.pack("<HH", ibkl[i], 0) for i in by_start)
        bkl = b"".join(struct.pack("<I", rs[i][1]) for i in by_end) + struct.pack("<I", last)
        # the tags follow the order of the starts
        self.atn_tag = {rs[i][2]: n for n, i in enumerate(by_start)}
        return sttb, bkf, bkl

    def atrd(self, refs, main):
        if not refs:
            return b""
        self.atn_ranges(refs, main)
        names = []
        for _cp, c in refs:
            a = c.get("author") or "Author"
            if a not in names:
                names.append(a)
        cps = [cp for cp, _c in refs] + [main.n + 1]
        tags = getattr(self, "atn_tag", {})
        items = []
        for k, (_cp, c) in enumerate(refs):
            ini = (c.get("initials") or "".join(w[:1] for w in (c.get("author") or "A").split()))[:9]
            xst = struct.pack("<H", len(ini)) + ini.encode("utf-16-le").ljust(18, b"\x00")
            items.append(xst + struct.pack("<HHHi", names.index(c.get("author") or "Author"), 0, 0, tags.get(k, -1)))
        return b"".join(struct.pack("<I", c) for c in cps) + b"".join(items)

    def bookmarks(self, st):
        if not st.bkf:
            return None
        names = []
        starts = []
        for cp, name in st.bkf:
            if name in names:
                continue
            names.append(name)
            starts.append(cp)
        ends = {}
        for cp, name in st.bkl:
            ends.setdefault(name, cp)
        # PlcfBkl in order of end position; each start names its end
        order = sorted(range(len(names)), key=lambda i: (ends.get(names[i], starts[i]), i))
        lim = [ends.get(names[i], starts[i]) for i in order]
        ibkl = {i: k for k, i in enumerate(order)}
        sttb = struct.pack("<HHH", 0xFFFF, len(names), 0) + b"".join(
            struct.pack("<H", len(n)) + n.encode("utf-16-le") for n in names)
        last = st.n
        idx = sorted(range(len(names)), key=lambda i: starts[i])
        # PlcfBkf must be ordered by position: the names follow the same order
        names = [names[i] for i in idx]
        sttb = struct.pack("<HHH", 0xFFFF, len(names), 0) + b"".join(
            struct.pack("<H", len(n)) + n.encode("utf-16-le") for n in names)
        bkf = b"".join(struct.pack("<I", starts[i]) for i in idx) + struct.pack("<I", last)
        bkf += b"".join(struct.pack("<HH", ibkl[i], 0) for i in idx)
        bkl = b"".join(struct.pack("<I", c) for c in lim) + struct.pack("<I", last)
        return sttb, bkf, bkl

    def dop(self):
        d = bytearray(500)
        d[0] = 0x02                          # fWidowControl
        if any((s.get("headers") or {}).get("even") or (s.get("footers") or {}).get("even") for s in self.doc.sections):
            d[0] |= 0x01                     # fFacingPages: different odd and even headers
        struct.pack_into("<H", d, 2, 1 << 2)  # nFtn = 1
        struct.pack_into("<H", d, 10, self.doc.tab_stop or 720)
        struct.pack_into("<H", d, 52, (1 << 2) | 3)   # nEdn = 1, roman numerals off
        return bytes(d)

    def fib(self, fclcb, ccp, cb_mac, fc_min=0x800, fc_mac=0x800, bte=((0, 0), (0, 0))):
        base = struct.pack("<HHHHH", 0xA5EC, 0x00C1, 0x6A62, 0x0409, 0)
        flags = 0x0200 | 0x1000                     # 1Table, extended characters
        if getattr(self, "template", False):
            flags |= 0x0001                         # fDot: a template
        base += struct.pack("<HHI", flags, 0x00BF, 0)
        base += struct.pack("<BBHHII", 0, 0, 0, 0, fc_min, fc_mac)
        assert len(base) == 32
        rgw = struct.pack("<H", 14) + b"\x00" * 26 + struct.pack("<H", 0x0409)
        lw = [0] * 22
        lw[0] = cb_mac
        lw[3] = ccp["text"]
        lw[4] = ccp["ftn"]
        lw[5] = ccp["hdd"]
        lw[7] = ccp["atn"]
        lw[8] = ccp["edn"]
        lw[11] = lw[14] = lw[17] = 0xFFFFF
        lw[12], lw[13] = bte[0]
        lw[15], lw[16] = bte[1]
        rglw = struct.pack("<H", 22) + struct.pack("<22i", *[v if v < 0x80000000 else v - (1 << 32) for v in lw])
        rgfc = struct.pack("<H", 93) + b"".join(struct.pack("<II", fc, lcb) for fc, lcb in fclcb)
        return base + rgw + rglw + rgfc + struct.pack("<H", 0)


def _as_png(data):
    """GIF, TIFF and other pictures a .doc can't hold as they are, converted to PNG."""
    try:
        import gi
        gi.require_version("GdkPixbuf", "2.0")
        from gi.repository import GdkPixbuf
        loader = GdkPixbuf.PixbufLoader()
        loader.write(data)
        loader.close()
        pb = loader.get_pixbuf()
        ok, buf = pb.save_to_bufferv("png", [], [])
        return bytes(buf) if ok else None
    except Exception:  # no loader for it: the picture is left out
        return None


def _cover(runs, total, default):
    """Runs sorted and with no holes from 0 to total."""
    out = []
    cp = 0
    for a, z, cx in sorted(runs):
        if a > cp:
            out.append((cp, a, default))
        if z > a:
            out.append((a, z, cx))
            cp = z
    if cp < total:
        out.append((cp, total, default))
    merged = []
    for r in out:
        if merged and merged[-1][2] == r[2] and merged[-1][1] == r[0]:
            merged[-1] = (merged[-1][0], r[1], r[2])
        else:
            merged.append(r)
    return merged


def _chpx_fkps(runs):
    """512-byte CHPX FKP pages for (fc0, fc1, grpprl) runs."""
    pages = []
    i = 0
    while i < len(runs):
        fcs = [runs[i][0]]
        offs = []
        heap = 511
        grp = {}
        j = i
        while j < len(runs):
            fc0, fc1, cx = runs[j]
            cx = cx[:255]
            need_off = 0
            if cx:
                if cx not in grp:
                    size = 1 + len(cx)
                    start = (heap - size) & ~1
                    if 4 * (len(fcs) + 1) + len(offs) + 1 > start:
                        break
                    grp[cx] = start
                    heap = start
                need_off = grp[cx] // 2
            if 4 * (len(fcs) + 1) + len(offs) + 1 > heap:
                break
            fcs.append(fc1)
            offs.append(need_off)
            j += 1
        if j == i:
            raise ValueError("a character run doesn't fit a page")
        page = bytearray(512)
        crun = len(offs)
        for k, fc in enumerate(fcs):
            struct.pack_into("<I", page, 4 * k, fc)
        for k, o in enumerate(offs):
            page[4 * (crun + 1) + k] = o
        for cx, start in grp.items():
            page[start] = len(cx)
            page[start + 1:start + 1 + len(cx)] = cx
        page[511] = crun
        pages.append((bytes(page), fcs[0], fcs[-1]))
        i = j
    return pages


def _papx_fkps(prs):
    """512-byte PAPX FKP pages for (fc0, fc1, istd, grpprl) paragraphs."""
    pages = []
    i = 0
    while i < len(prs):
        fcs = [prs[i][0]]
        bxs = []
        heap = 511
        grp = {}
        j = i
        while j < len(prs):
            fc0, fc1, istd, px = prs[j]
            body = struct.pack("<H", istd) + px
            if len(body) % 2:
                enc = struct.pack("<B", (len(body) + 1) // 2) + body      # 2*cb - 1 bytes
            else:
                enc = struct.pack("<BB", 0, len(body) // 2) + body         # cb = 0, then 2*cb' bytes
            key = enc
            if key not in grp:
                start = (heap - len(enc)) & ~1
                if 4 * (len(fcs) + 1) + 13 * (len(bxs) + 1) > start:
                    break
                grp[key] = start
                heap = start
            if 4 * (len(fcs) + 1) + 13 * (len(bxs) + 1) > heap:
                break
            fcs.append(fc1)
            bxs.append(grp[key] // 2)
            j += 1
        if j == i:
            raise ValueError("a paragraph's properties don't fit a page")
        page = bytearray(512)
        cpara = len(bxs)
        for k, fc in enumerate(fcs):
            struct.pack_into("<I", page, 4 * k, fc)
        for k, o in enumerate(bxs):
            page[4 * (cpara + 1) + 13 * k] = o
        for enc, start in grp.items():
            page[start:start + len(enc)] = enc
        page[511] = cpara
        pages.append((bytes(page), fcs[0], fcs[-1]))
        i = j
    return pages


def _plc_bte(btes):
    if not btes:
        return b""
    fcs = [b[0] for b in btes] + [btes[-1][1]]
    return b"".join(struct.pack("<I", f) for f in fcs) + b"".join(struct.pack("<I", b[2]) for b in btes)


def _plcfld(fields, _base, end):
    if not fields:
        return b""
    cps = [cp for cp, _k, _v in fields] + [end]
    flds = []
    depth = 0
    for cp, kind, v in fields:
        if kind == 0x13:
            flds.append(struct.pack("<BB", 0x13, v & 0xFF))
            depth += 1
        elif kind == 0x14:
            flds.append(struct.pack("<BB", 0x14, 0))
        else:
            depth -= 1
            flds.append(struct.pack("<BB", 0x15, 0x80 | (0x40 if depth > 0 else 0)))
    return b"".join(struct.pack("<I", c) for c in cps) + b"".join(flds)


def _summary(meta):
    """\\x05SummaryInformation: title, subject, author, keywords, comments (as Word writes them)."""
    props = []
    for pid, key in ((2, "title"), (3, "subject"), (4, "creator"), (5, "keywords"), (6, "description")):
        v = meta.get(key)
        if v:
            props.append((pid, v))
    props.append((18, "Folio Page"))
    body = []
    entries = []
    off = 8 + 8 * (len(props) + 1)
    cp = struct.pack("<IH", 2, 1200) + b"\x00\x00"
    entries.append((1, off))
    body.append(cp)
    off += len(cp)
    for pid, v in props:
        data = (v + "\x00").encode("utf-16-le")
        blob = struct.pack("<II", 31, len(v) + 1) + data
        while len(blob) % 4:
            blob += b"\x00"
        entries.append((pid, off))
        body.append(blob)
        off += len(blob)
    section = struct.pack("<II", off, len(entries)) + b"".join(struct.pack("<II", p, o) for p, o in entries) + b"".join(body)
    fmtid = bytes.fromhex("e0859ff2f94f6810ab9108002b27b3d9")
    head = struct.pack("<HHI", 0xFFFE, 0, 0x00020006) + b"\x00" * 16 + struct.pack("<I", 1) + fmtid + struct.pack("<I", 48)
    return head + section


# ------------------------------------------------------------------ compound file
def cfb(streams):
    """A compound file (version 3, 512-byte sectors) holding the given streams."""
    SEC = 512
    names = list(streams)
    mini = bytearray()
    minifat = []
    big = []        # (name, data) in regular sectors
    starts = {}
    for n in names:
        data = streams[n]
        if len(data) < 4096:
            start = len(mini) // 64
            k = (len(data) + 63) // 64
            for i in range(k):
                minifat.append(start + i + 1 if i < k - 1 else 0xFFFFFFFE)
            if k == 0:
                start = 0xFFFFFFFE
            starts[n] = ("mini", start)
            mini += data.ljust(k * 64, b"\x00")
        else:
            big.append(n)
    sectors = []     # list of 512-byte chunks (data)
    fat = []

    def alloc(data):
        k = max(1, (len(data) + SEC - 1) // SEC)
        first = len(sectors)
        for i in range(k):
            sectors.append(bytes(data[i * SEC:(i + 1) * SEC]).ljust(SEC, b"\x00"))
            fat.append(first + i + 1 if i < k - 1 else 0xFFFFFFFE)
        return first
    for n in big:
        starts[n] = ("big", alloc(streams[n]))
    mini_start = alloc(mini) if mini else 0xFFFFFFFE
    minifat_bytes = b"".join(struct.pack("<I", v) for v in minifat)
    minifat_start = alloc(minifat_bytes) if minifat else 0xFFFFFFFE
    # directory: root, then the streams as a balanced tree under it
    entries = [("Root Entry", 5, mini_start if mini else 0xFFFFFFFE, len(mini))]
    for n in names:
        kind, st = starts[n]
        entries.append((n, 2, st, len(streams[n])))

    def key(name):
        return (len(name), name.upper())
    order = sorted(range(1, len(entries)), key=lambda i: key(entries[i][0]))
    left = {}
    right = {}

    def build(lo, hi):
        if lo > hi:
            return 0xFFFFFFFF
        mid = (lo + hi) // 2
        node = order[mid]
        left[node] = build(lo, mid - 1)
        right[node] = build(mid + 1, hi)
        return node
    root_child = build(0, len(order) - 1)
    dir_bytes = bytearray()
    for i, (name, typ, start, size) in enumerate(entries):
        nm = (name + "\x00").encode("utf-16-le")
        e = nm.ljust(64, b"\x00") + struct.pack("<HBB", len(nm), typ, 1)
        if i == 0:
            e += struct.pack("<III", 0xFFFFFFFF, 0xFFFFFFFF, root_child)
        else:
            e += struct.pack("<III", left.get(i, 0xFFFFFFFF), right.get(i, 0xFFFFFFFF), 0xFFFFFFFF)
        e += b"\x00" * 16 + struct.pack("<I", 0) + b"\x00" * 16
        e += struct.pack("<II", start if start is not None else 0xFFFFFFFE, size) + b"\x00" * 4
        dir_bytes += e
    while len(dir_bytes) % SEC:
        dir_bytes += (b"\x00" * 64 + struct.pack("<HBB", 0, 0, 0) + struct.pack("<III", 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF)
                      + b"\x00" * 52)[:128]
    dir_start = alloc(dir_bytes)
    # the FAT itself: sectors marked FATSECT
    nsec = len(sectors)
    nfat = 1
    while (nsec + nfat) > nfat * 128:
        nfat += 1
    if nfat > 109:
        raise ValueError("document too large for this writer")
    fat_start = len(sectors)
    for i in range(nfat):
        fat.append(0xFFFFFFFD)
    fat_bytes = b"".join(struct.pack("<I", v) for v in fat).ljust(nfat * SEC, b"\xff")
    for i in range(nfat):
        sectors.append(fat_bytes[i * SEC:(i + 1) * SEC])
    hdr = bytearray(512)
    hdr[0:8] = bytes.fromhex("d0cf11e0a1b11ae1")
    struct.pack_into("<HHHHH", hdr, 24, 0x003E, 0x0003, 0xFFFE, 9, 6)
    struct.pack_into("<I", hdr, 44, nfat)
    struct.pack_into("<I", hdr, 48, dir_start)
    struct.pack_into("<I", hdr, 52, 0)
    struct.pack_into("<I", hdr, 56, 4096)
    struct.pack_into("<I", hdr, 60, minifat_start)
    struct.pack_into("<I", hdr, 64, (len(minifat_bytes) + SEC - 1) // SEC if minifat else 0)
    struct.pack_into("<I", hdr, 68, 0xFFFFFFFE)
    struct.pack_into("<I", hdr, 72, 0)
    for i in range(109):
        struct.pack_into("<I", hdr, 76 + 4 * i, fat_start + i if i < nfat else 0xFFFFFFFF)
    return bytes(hdr) + b"".join(sectors)


def to_doc(doc, template=False):
    w = Writer(doc)
    w.template = template
    return w.write()


def docx_to_doc_file(docx_path, doc_path, template=False):
    from . import docxread
    data = to_doc(docxread.read(docx_path), template)
    with open(doc_path, "wb") as fh:
        fh.write(data)
    return doc_path
