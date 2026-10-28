"""Word 97-2003 documents (.doc, .dot) read by Folio itself into the shared document
model (docxbuild.Doc). Written from Microsoft's published [MS-DOC] and [MS-CFB]
specifications; nothing is converted by another program."""
import struct
import zlib

from . import docxbuild as B


class Unsupported(Exception):
    """A file this reader doesn't handle (Word 95 and older, encrypted files)."""


# ------------------------------------------------------------------ compound file
class CFB:
    """A Compound File Binary container: its streams by name."""

    def __init__(self, data):
        if data[:8] != b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
            raise Unsupported("not a Word 97-2003 document")
        self.data = data
        ss = 1 << struct.unpack_from("<H", data, 0x1E)[0]
        mss = 1 << struct.unpack_from("<H", data, 0x20)[0]
        self.ss, self.mss = ss, mss
        nfat, first_dir = struct.unpack_from("<II", data, 0x2C)
        self.cutoff = struct.unpack_from("<I", data, 0x38)[0]
        first_mf, nmf, first_difat, ndifat = struct.unpack_from("<IIII", data, 0x3C)
        difat = list(struct.unpack_from("<109I", data, 0x4C))
        sec = first_difat
        guard = 0
        while ndifat and sec < 0xFFFFFFFA and guard < 10000:
            off = 512 + sec * ss if ss == 512 else ss + sec * ss
            vals = struct.unpack_from("<%dI" % (ss // 4), data, self._off(sec))
            difat.extend(vals[:-1])
            sec = vals[-1]
            ndifat -= 1
            guard += 1
        self.fat = []
        for s in difat[:nfat]:
            if s >= 0xFFFFFFFA:
                continue
            self.fat.extend(struct.unpack_from("<%dI" % (ss // 4), data, self._off(s)))
        self.minifat = []
        if nmf and first_mf < 0xFFFFFFFA:
            raw = self._chain(first_mf)
            self.minifat = list(struct.unpack("<%dI" % (len(raw) // 4), raw))
        dirs = self._chain(first_dir)
        self.entries = []
        for i in range(len(dirs) // 128):
            e = dirs[i * 128:(i + 1) * 128]
            nlen = struct.unpack_from("<H", e, 64)[0]
            name = e[:max(0, nlen - 2)].decode("utf-16-le", "replace")
            typ = e[66]
            start = struct.unpack_from("<I", e, 116)[0]
            size = struct.unpack_from("<Q", e, 120)[0]
            if ss == 512:
                size &= 0xFFFFFFFF
            self.entries.append((name, typ, start, size))
        root = self.entries[0] if self.entries else None
        self.ministream = self._chain(root[2])[:root[3]] if root and root[2] < 0xFFFFFFFA else b""

    def _off(self, sec):
        return (sec + 1) * self.ss

    def _chain(self, start, limit=None):
        out = []
        sec = start
        seen = 0
        n = len(self.fat)
        while sec < 0xFFFFFFFA and seen <= n:
            o = self._off(sec)
            out.append(self.data[o:o + self.ss])
            sec = self.fat[sec] if sec < n else 0xFFFFFFFE
            seen += 1
        return b"".join(out)

    def _minichain(self, start):
        out = []
        sec = start
        seen = 0
        n = len(self.minifat)
        while sec < 0xFFFFFFFA and seen <= n:
            o = sec * self.mss
            out.append(self.ministream[o:o + self.mss])
            sec = self.minifat[sec] if sec < n else 0xFFFFFFFE
            seen += 1
        return b"".join(out)

    def stream(self, name):
        for n, typ, start, size in self.entries:
            if typ == 2 and n == name:
                if size < self.cutoff:
                    return self._minichain(start)[:size]
                return self._chain(start)[:size]
        return None


# ------------------------------------------------------------------ helpers
def u8(b, o):
    return b[o] if 0 <= o < len(b) else 0


def u16(b, o):
    return struct.unpack_from("<H", b, o)[0] if o + 2 <= len(b) else 0


def i16(b, o):
    return struct.unpack_from("<h", b, o)[0] if o + 2 <= len(b) else 0


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0] if o + 4 <= len(b) else 0


def i32(b, o):
    return struct.unpack_from("<i", b, o)[0] if o + 4 <= len(b) else 0


ICO = {0: None, 1: "000000", 2: "0000FF", 3: "00FFFF", 4: "00FF00", 5: "FF00FF", 6: "FF0000",
       7: "FFFF00", 8: "FFFFFF", 9: "000080", 10: "008080", 11: "008000", 12: "800080",
       13: "800000", 14: "808000", 15: "808080", 16: "C0C0C0"}
HIGHLIGHT = {1: "black", 2: "blue", 3: "cyan", 4: "green", 5: "magenta", 6: "red", 7: "yellow",
             8: "white", 9: "darkBlue", 10: "darkCyan", 11: "darkGreen", 12: "darkMagenta",
             13: "darkRed", 14: "darkYellow", 15: "darkGray", 16: "lightGray"}
KUL = {0: "none", 1: "single", 2: "words", 3: "double", 4: "dotted", 6: "thick", 7: "dash",
       9: "dotDash", 10: "dotDotDash", 11: "wave", 20: "dottedHeavy", 23: "dashedHeavy",
       25: "dashDotHeavy", 26: "dashDotDotHeavy", 27: "wavyHeavy", 39: "dashLong", 43: "wavyDouble",
       55: "dashLongHeavy"}
NFC = {0: "decimal", 1: "upperRoman", 2: "lowerRoman", 3: "upperLetter", 4: "lowerLetter",
       5: "ordinal", 6: "cardinalText", 7: "ordinalText", 22: "decimalZero", 23: "bullet",
       255: "none", 47: "none"}
BRC_TYPE = {1: "single", 2: "thick", 3: "double", 5: "single", 6: "dotted", 7: "dashed",
            8: "dotDash", 9: "dotDotDash", 10: "triple", 22: "dashSmallGap"}


def colorref(v):
    """A COLORREF (0x00bbggrr), or None for 'auto'."""
    if v & 0xFF000000:
        return None
    r, g, b = v & 0xFF, (v >> 8) & 0xFF, (v >> 16) & 0xFF
    return "%02X%02X%02X" % (r, g, b)


def sprms(grpprl):
    """(opcode, operand bytes) of a grpprl."""
    i = 0
    n = len(grpprl)
    while i + 2 <= n:
        op = u16(grpprl, i)
        i += 2
        spra = op >> 13
        if spra in (0, 1):
            size = 1
        elif spra in (2, 4, 5):
            size = 2
        elif spra == 3:
            size = 4
        elif spra == 7:
            size = 3
        else:
            if op == 0xD608 or op == 0xD606:       # sprmTDefTable: 2-byte length
                size = u16(grpprl, i) + 1
                yield op, grpprl[i + 2:i + 1 + size]
                i += 1 + size
                continue
            if op == 0xC615:                       # sprmPChgTabs
                size = u8(grpprl, i)
                if size == 255:
                    dmax = u8(grpprl, i + 1)
                    amax = u8(grpprl, i + 2 + dmax * 4)
                    size = 1 + dmax * 4 + 1 + amax * 3
                yield op, grpprl[i + 1:i + 1 + size]
                i += 1 + size
                continue
            size = u8(grpprl, i)
            yield op, grpprl[i + 1:i + 1 + size]
            i += 1 + size
            continue
        yield op, grpprl[i:i + size]
        i += size


def brc(b, o, new):
    """A border: (eighths of a point, colour, kind, space) or None."""
    if new:
        cv = u32(b, o)
        w = u8(b, o + 4)
        t = u8(b, o + 5)
        sp = u8(b, o + 6) & 0x1F
        if t in (0, 0xFF) or w == 0 and t == 0:
            return None
        return (max(2, w), colorref(cv) or "000000", BRC_TYPE.get(t, "single"), sp)
    w = u8(b, o)
    t = u8(b, o + 1)
    ico = u8(b, o + 2)
    sp = u8(b, o + 3) & 0x1F
    if t in (0, 0xFF) or (w == 0xFF and t == 0xFF):
        return None
    return (max(2, w), ICO.get(ico) or "000000", BRC_TYPE.get(t, "single"), sp)


def shd(b, o, new):
    if new:
        back = u32(b, o + 4)
        return colorref(back)
    v = u16(b, o)
    back = (v >> 5) & 0x1F
    pat = v >> 10
    if pat == 0 and back == 0:
        return None
    return ICO.get(back)


# ------------------------------------------------------------------ properties
def apply_chp(r, grpprl, base=None, fonts=None, chpx_extra=None):
    """Character sprms into run properties r (base: the style's for toggles)."""
    base = base or {}
    for op, a in sprms(grpprl):
        if op in (0x0835, 0x0836, 0x0837, 0x0838, 0x0839, 0x083A, 0x083B, 0x083C, 0x0854, 0x0858, 0x2A53):
            key = {0x0835: "b", 0x0836: "i", 0x0837: "strike", 0x0838: "outline", 0x0839: "shadow",
                   0x083A: "smallcaps", 0x083B: "caps", 0x083C: "hidden", 0x0854: "emboss",
                   0x0858: "imprint", 0x2A53: "dstrike"}[op]
            v = u8(a, 0)
            if v in (0, 1):
                r[key] = bool(v)
            elif v == 0x80:
                r[key] = bool(base.get(key))
            elif v == 0x81:
                r[key] = not base.get(key)
        elif op == 0x2A3E:
            r["u"] = KUL.get(u8(a, 0), "single")
        elif op == 0x2A42:
            c = ICO.get(u8(a, 0))
            if c:
                r["color"] = c
            else:
                r.pop("color", None)
        elif op == 0x6870:
            c = colorref(u32(a, 0))
            if c:
                r["color"] = c
        elif op == 0x4A43:
            r["sz"] = u16(a, 0)
        elif op in (0x4A4F, 0x4A50, 0x4A51, 0x4A5E):
            if fonts is not None:
                idx = u16(a, 0)
                if idx < len(fonts):
                    k = {0x4A4F: "font", 0x4A50: "font_ea", 0x4A51: "_font2", 0x4A5E: "font_cs"}[op]
                    r[k] = fonts[idx]
        elif op == 0x2A48:
            iss = u8(a, 0)
            r["vert"] = {1: "superscript", 2: "subscript"}.get(iss, "baseline")
        elif op == 0x2A0C:
            h = HIGHLIGHT.get(u8(a, 0))
            if h:
                r["highlight"] = h
            else:
                r.pop("highlight", None)
        elif op == 0x8840:
            r["spacing"] = i16(a, 0)
        elif op == 0x4852:
            r["scale"] = u16(a, 0)
        elif op == 0x4845:
            r["position"] = i16(a, 0)
        elif op == 0xCA71:
            c = shd(a, 0, True)
            if c:
                r["shd"] = c
        elif op == 0x4866:
            c = shd(a, 0, False)
            if c:
                r["shd"] = c
        elif op == 0x4A30:
            r["_istd"] = u16(a, 0)
        elif op == 0x6A03:
            r["_pic"] = u32(a, 0)
        elif op == 0x0855:
            r["_spec"] = bool(u8(a, 0))
        elif op == 0x0806:
            r["_data"] = bool(u8(a, 0))
        elif op == 0x080A:
            r["_ole"] = bool(u8(a, 0))
        elif op == 0x0800:
            r["_rmdel"] = bool(u8(a, 0))
        elif op == 0x0801:
            r["_rmark"] = bool(u8(a, 0))
    return r


def apply_pap(p, grpprl):
    for op, a in sprms(grpprl):
        if op in (0x2403, 0x2461):
            p["align"] = {0: "left", 1: "center", 2: "right", 3: "both", 4: "distribute",
                          5: "both", 7: "both", 8: "both"}.get(u8(a, 0), "left")
        elif op in (0x845E, 0x840F):
            p["ind_l"] = i16(a, 0)
        elif op in (0x845D, 0x840E):
            p["ind_r"] = i16(a, 0)
        elif op in (0x8460, 0x8411):
            p["ind_first"] = i16(a, 0)
        elif op == 0xA413:
            p["sb"] = u16(a, 0)
        elif op == 0xA414:
            p["sa"] = u16(a, 0)
        elif op == 0x6412:
            dya = i16(a, 0)
            mult = i16(a, 2)
            if mult:
                p["line"] = abs(dya)
                p["line_rule"] = "auto"
            elif dya < 0:
                p["line"] = -dya
                p["line_rule"] = "exact"
            else:
                p["line"] = dya
                p["line_rule"] = "atLeast"
        elif op == 0x2405:
            p["keep_lines"] = bool(u8(a, 0))
        elif op == 0x2406:
            p["keep_next"] = bool(u8(a, 0))
        elif op == 0x2407:
            p["pbb"] = bool(u8(a, 0))
        elif op == 0x2431:
            p["widow"] = bool(u8(a, 0))
        elif op == 0x460B:
            p["_ilfo"] = u16(a, 0)
        elif op == 0x260A:
            p["_ilvl"] = u8(a, 0)
        elif op == 0x2640:
            lv = u8(a, 0)
            if lv < 9:
                p["outline"] = lv
            else:
                p.pop("outline", None)
        elif op == 0x2416:
            p["_intable"] = bool(u8(a, 0))
        elif op == 0x2417:
            p["_ttp"] = bool(u8(a, 0))
        elif op == 0x6649:
            p["_itap"] = u32(a, 0)
        elif op == 0x664A:
            p["_itap"] = max(0, p.get("_itap", 1) + i32(a, 0))
        elif op == 0x244B:
            p["_innercell"] = bool(u8(a, 0))
        elif op == 0x244C:
            p["_innerttp"] = bool(u8(a, 0))
        elif op in (0xC60D, 0xC615):
            tabs = dict((t[0], t) for t in p.get("tabs", []))
            nd = u8(a, 0)
            for k in range(nd):
                tabs.pop(i16(a, 1 + 2 * k), None)
            o = 1 + 2 * nd
            if op == 0xC615:
                o = 1 + 4 * nd
            na = u8(a, o)
            for k in range(na):
                pos = i16(a, o + 1 + 2 * k)
                tbd = u8(a, o + 1 + 2 * na + k)
                jc = {0: "left", 1: "center", 2: "right", 3: "decimal", 4: "bar"}.get(tbd & 7, "left")
                lead = {1: "dot", 2: "hyphen", 3: "underscore", 4: "heavy", 5: "middleDot"}.get((tbd >> 3) & 7)
                tabs[pos] = (pos, jc, lead)
            p["tabs"] = [tabs[k] for k in sorted(tabs)]
        elif op == 0x442D:
            c = shd(a, 0, False)
            if c:
                p["shd"] = c
        elif op == 0xC64D:
            c = shd(a, 0, True)
            if c:
                p["shd"] = c
        elif op in (0x6424, 0x6425, 0x6426, 0x6427):
            side = {0x6424: "top", 0x6425: "left", 0x6426: "bottom", 0x6427: "right"}[op]
            v = brc(a, 0, False)
            if v:
                p.setdefault("borders", {})[side] = v
        elif op in (0xC64E, 0xC64F, 0xC650, 0xC651):
            side = {0xC64E: "top", 0xC64F: "left", 0xC650: "bottom", 0xC651: "right"}[op]
            v = brc(a, 0, True)
            if v:
                p.setdefault("borders", {})[side] = v
        elif op == 0x2441:
            p["bidi"] = bool(u8(a, 0))
        elif op == 0x246D:
            p["contextual"] = bool(u8(a, 0))
    return p


# ------------------------------------------------------------------ the reader
class Reader:
    def __init__(self, path):
        with open(path, "rb") as fh:
            data = fh.read()
        self.cfb = CFB(data)
        wd = self.cfb.stream("WordDocument")
        if not wd:
            raise Unsupported("not a Word document")
        self.wd = wd
        if u16(wd, 0) in (0xA5DC, 0xA5DB):
            raise Unsupported("Word 95")
        if u16(wd, 0) != 0xA5EC:
            raise Unsupported("not a Word document")
        self.nfib = u16(wd, 2)
        flags = u16(wd, 0x0A)
        if flags & 0x0100:
            raise Unsupported("encrypted")
        if self.nfib < 0x00C1:
            raise Unsupported("Word 95")
        tname = "1Table" if flags & 0x0200 else "0Table"
        self.tbl = self.cfb.stream(tname) or b""
        self.data_stream = self.cfb.stream("Data") or b""
        o = 32
        csw = u16(wd, o)
        o += 2 + csw * 2
        cslw = u16(wd, o)
        self.lw = [i32(wd, o + 2 + 4 * k) for k in range(cslw)]
        o += 2 + cslw * 4
        cb = u16(wd, o)
        self.fclcb = [(u32(wd, o + 2 + 8 * k), u32(wd, o + 6 + 8 * k)) for k in range(cb)]
        self.doc = B.Doc()

    def fl(self, idx):
        return self.fclcb[idx] if idx < len(self.fclcb) else (0, 0)

    def tbl_part(self, idx):
        fc, lcb = self.fl(idx)
        return self.tbl[fc:fc + lcb] if lcb else b""

    # ------------------------------------------------------------ text
    def read_pieces(self):
        clx = self.tbl_part(33)
        i = 0
        self.pieces = []
        while i < len(clx):
            t = clx[i]
            if t == 1:
                cb = u16(clx, i + 1)
                i += 3 + cb
            elif t == 2:
                lcb = u32(clx, i + 1)
                plc = clx[i + 5:i + 5 + lcb]
                n = (lcb - 4) // 12
                cps = [u32(plc, 4 * k) for k in range(n + 1)]
                for k in range(n):
                    pcd = 4 * (n + 1) + 8 * k
                    fc = u32(plc, pcd + 2)
                    prm = u16(plc, pcd + 6)
                    compressed = bool(fc & 0x40000000)
                    fc &= 0x3FFFFFFF
                    if compressed:
                        fc //= 2
                    self.pieces.append((cps[k], cps[k + 1], fc, compressed, prm))
                break
            else:
                break
        if not self.pieces:
            # a non-complex file: one piece
            fcmin = u32(self.wd, 0x18)
            fcmac = u32(self.wd, 0x1C)
            self.pieces.append((0, fcmac - fcmin, fcmin, True, 0))
        chars = []
        for cp0, cp1, fc, comp, prm in self.pieces:
            n = cp1 - cp0
            if comp:
                raw = self.wd[fc:fc + n]
                chars.append(raw.decode("cp1252", "replace"))
            else:
                raw = self.wd[fc:fc + 2 * n]
                chars.append(raw.decode("utf-16-le", "replace"))
        self.text = "".join(chars)

    def fc_of(self, cp):
        """(fc, compressed) for a character position."""
        for cp0, cp1, fc, comp, prm in self.pieces:
            if cp0 <= cp < cp1:
                return (fc + (cp - cp0) * (1 if comp else 2)), comp, prm
        return None, False, 0

    # ------------------------------------------------------------ fkp tables
    def read_fkps(self):
        self.chpx_runs = []   # (fc0, fc1, grpprl)
        plc = self.tbl_part(12)
        n = (len(plc) - 4) // 8
        for k in range(n):
            pn = u32(plc, 4 * (n + 1) + 4 * k) & 0x3FFFFF
            page = self.wd[pn * 512:pn * 512 + 512]
            if len(page) < 512:
                continue
            crun = page[511]
            for j in range(crun):
                fc0 = u32(page, 4 * j)
                fc1 = u32(page, 4 * (j + 1))
                off = page[4 * (crun + 1) + j] * 2
                if off:
                    cb = page[off]
                    self.chpx_runs.append((fc0, fc1, page[off + 1:off + 1 + cb]))
                else:
                    self.chpx_runs.append((fc0, fc1, b""))
        self.chpx_runs.sort(key=lambda x: x[0])
        self.papx_runs = []
        plc = self.tbl_part(13)
        n = (len(plc) - 4) // 8
        for k in range(n):
            pn = u32(plc, 4 * (n + 1) + 4 * k) & 0x3FFFFF
            page = self.wd[pn * 512:pn * 512 + 512]
            if len(page) < 512:
                continue
            cpara = page[511]
            for j in range(cpara):
                fc0 = u32(page, 4 * j)
                fc1 = u32(page, 4 * (j + 1))
                bx = 4 * (cpara + 1) + 13 * j
                off = page[bx] * 2
                if not off:
                    self.papx_runs.append((fc0, fc1, 0, b""))
                    continue
                cb = page[off]
                if cb == 0:
                    cb2 = page[off + 1]
                    body = page[off + 2:off + 2 + 2 * cb2]
                else:
                    body = page[off + 1:off + 2 * cb]
                istd = u16(body, 0)
                self.papx_runs.append((fc0, fc1, istd, body[2:]))
        self.papx_runs.sort(key=lambda x: x[0])
        import bisect
        self._chpx_starts = [r[0] for r in self.chpx_runs]
        self._papx_starts = [r[0] for r in self.papx_runs]
        self._bisect = bisect

    def chpx_at(self, fc):
        i = self._bisect.bisect_right(self._chpx_starts, fc) - 1
        if 0 <= i < len(self.chpx_runs):
            r = self.chpx_runs[i]
            if r[0] <= fc < r[1]:
                return r
        return None

    def papx_at(self, fc):
        i = self._bisect.bisect_right(self._papx_starts, fc) - 1
        if 0 <= i < len(self.papx_runs):
            r = self.papx_runs[i]
            if r[0] <= fc < r[1]:
                return r
        return None

    def prm_sprms(self, prm):
        """The sprms a piece descriptor carries (Prm)."""
        if not prm:
            return b""
        if prm & 1:
            igrpprl = prm >> 1
            return self.grpprls[igrpprl] if igrpprl < len(self.grpprls) else b""
        isprm = (prm >> 1) & 0x7F
        val = prm >> 8
        # the 128 single-byte sprms Prm0 can name
        table = {0x08: 0x0835, 0x09: 0x0836, 0x0A: 0x0837, 0x0B: 0x0838, 0x0C: 0x0839, 0x0D: 0x083A,
                 0x0E: 0x083B, 0x0F: 0x083C, 0x10: 0x2A3E, 0x12: 0x2A42}
        op = table.get(isprm)
        if not op:
            return b""
        return struct.pack("<HB", op, val & 0xFF)

    def read_grpprls(self):
        clx = self.tbl_part(33)
        self.grpprls = []
        i = 0
        while i < len(clx) and clx[i] == 1:
            cb = u16(clx, i + 1)
            self.grpprls.append(clx[i + 3:i + 3 + cb])
            i += 3 + cb

    # ------------------------------------------------------------ fonts and styles
    def read_fonts(self):
        b = self.tbl_part(15)
        self.fonts = []
        if not b:
            return
        n = u16(b, 0)
        extended = n == 0xFFFF
        if extended:
            n = u16(b, 2)
            o = 6
        else:
            o = 4
        for _ in range(n):
            cch = b[o] if o < len(b) else 0
            ffn = b[o + 1:o + 1 + cch]
            name = ffn[39:].decode("utf-16-le", "replace") if len(ffn) > 40 else ""
            name = name.split("\x00")[0]
            self.fonts.append(name or "Times New Roman")
            o += 1 + cch

    def read_styles(self):
        b = self.tbl_part(1)
        self.styles = {}
        if not b:
            return
        cbstshi = u16(b, 0)
        stshi = b[2:2 + cbstshi]
        cstd = u16(stshi, 0)
        cbbase = u16(stshi, 2)
        self.default_ftc = [u16(stshi, 12 + 2 * k) for k in range(3)]
        o = 2 + cbstshi
        raw = {}
        for istd in range(cstd):
            if o + 2 > len(b):
                break
            cb = u16(b, o)
            std = b[o + 2:o + 2 + cb]
            o += 2 + cb
            if not cb:
                continue
            sti = u16(std, 0) & 0x0FFF
            w2 = u16(std, 2)
            stk = w2 & 0x0F
            base = w2 >> 4
            w3 = u16(std, 4)
            cupx = w3 & 0x0F
            nxt = w3 >> 4
            p = cbbase
            cch = u16(std, p)
            name = std[p + 2:p + 2 + 2 * cch].decode("utf-16-le", "replace")
            p += 2 + 2 * cch + 2
            upx = []
            for _ in range(cupx):
                if p % 2:
                    p += 1
                cbu = u16(std, p)
                upx.append(std[p + 2:p + 2 + cbu])
                p += 2 + cbu
            raw[istd] = {"sti": sti, "stk": stk, "base": base if base != 0xFFF else None,
                         "next": nxt if nxt != 0xFFF else None, "name": name, "upx": upx}
        self.raw_styles = raw

    def style_props(self, istd, depth=0):
        """(paragraph props, run props) of a style with what it inherits."""
        cache = self.__dict__.setdefault("_sp", {})
        if istd in cache:
            return cache[istd]
        s = self.raw_styles.get(istd)
        if s is None or depth > 20:
            return {}, {}
        if s["base"] is not None and s["base"] != istd:
            pp, rp = self.style_props(s["base"], depth + 1)
            pp, rp = dict(pp), dict(rp)
        else:
            pp, rp = {}, {}
        if s["stk"] == 1 and len(s["upx"]) >= 2:
            apply_pap(pp, s["upx"][0][2:])
            apply_chp(rp, s["upx"][1], dict(rp), self.fonts)
        elif s["stk"] == 2 and s["upx"]:
            apply_chp(rp, s["upx"][0], dict(rp), self.fonts)
        cache[istd] = (pp, rp)
        return pp, rp

    def style_own(self, istd):
        """A style's own properties (not inherited), for the document model."""
        s = self.raw_styles.get(istd)
        pp, rp = {}, {}
        if s is None:
            return pp, rp
        base_rp = self.style_props(s["base"])[1] if s["base"] is not None else {}
        if s["stk"] == 1 and len(s["upx"]) >= 2:
            apply_pap(pp, s["upx"][0][2:])
            apply_chp(rp, s["upx"][1], base_rp, self.fonts)
        elif s["stk"] == 2 and s["upx"]:
            apply_chp(rp, s["upx"][0], base_rp, self.fonts)
        return pp, rp

    def build_styles(self):
        d = self.doc
        self.style_ids = {}
        used = set()
        for istd, s in sorted(self.raw_styles.items()):
            if s["stk"] not in (1, 2, 3):
                continue
            name = s["name"].split(",")[0] or "Style%d" % istd
            disp = name
            for k in B.BUILTIN:
                if k.lower() == name.lower():
                    disp = k
                    break
            if istd == 0:
                disp = "Normal"
            sid = B.style_id(disp)
            if s["stk"] == 2 and istd == 10:
                sid = "DefaultParagraphFont"
            while sid in used:
                sid += "1"
            used.add(sid)
            self.style_ids[istd] = sid
        for istd, s in sorted(self.raw_styles.items()):
            if istd not in self.style_ids:
                continue
            sid = self.style_ids[istd]
            kind = {1: "paragraph", 2: "character", 3: "table"}[s["stk"]]
            pp, rp = self.style_own(istd)
            pp = {k: v for k, v in pp.items() if not k.startswith("_")}
            rp = {k: v for k, v in rp.items() if not k.startswith("_")}
            if kind == "table":
                pp, rp = {}, {}
            st = d.add_style(sid, B.BUILTIN and self._display(s, istd), kind,
                             based=self.style_ids.get(s["base"]) if s["base"] is not None else None,
                             nxt=self.style_ids.get(s["next"]) if s["next"] is not None else None,
                             ppr=pp, rpr=rp, default=(istd == 0 or (kind == "character" and istd == 10)))
            if istd == 0:
                st["default"] = True
        d.defaults["rpr"] = {"sz": 20, "font": self.fonts[self.default_ftc[0]] if self.fonts and self.default_ftc[0] < len(self.fonts) else "Times New Roman"}
        if not d.style("Normal"):
            d.add_style("Normal", "Normal", default=True)

    def _display(self, s, istd):
        name = s["name"].split(",")[0]
        for k in B.BUILTIN:
            if k.lower() == name.lower():
                return k
        return "Normal" if istd == 0 else (name or "Style%d" % istd)

    # ------------------------------------------------------------ lists
    def read_lists(self):
        b = self.tbl_part(73)
        self.lsts = {}
        if b:
            n = u16(b, 0)
            o = 2
            lstfs = []
            for _ in range(n):
                lsid = i32(b, o)
                simple = bool(b[o + 26] & 1) if o + 26 < len(b) else False
                lstfs.append((lsid, simple))
                o += 28
            p = self.fl(73)[0] + self.fl(73)[1]
            for lsid, simple in lstfs:
                levels = []
                for li in range(1 if simple else 9):
                    lvl, p = self.read_lvl(self.tbl, p, li)
                    levels.append(lvl)
                while len(levels) < 9:
                    levels.append({"fmt": "decimal", "text": "%%%d." % (len(levels) + 1),
                                   "ind": 720 * (len(levels) + 1), "hang": 360})
                self.lsts[lsid] = levels
        b = self.tbl_part(74)
        self.lfos = []
        if b:
            n = u32(b, 0)
            o = 4
            lfos = []
            for _ in range(n):
                lfos.append((i32(b, o), b[o + 12] if o + 12 < len(b) else 0))
                o += 16
            p = self.fl(74)[0] + self.fl(74)[1]
            tbl = self.tbl
            for lsid, clfolvl in lfos:
                over = {}
                p += 4
                for _ in range(clfolvl):
                    start = i32(tbl, p)
                    fl = u32(tbl, p + 4)
                    p += 8
                    ilvl = fl & 0x0F
                    item = {}
                    if fl & 0x10:
                        item["start"] = start
                    if fl & 0x20:
                        lvl, p = self.read_lvl(tbl, p, ilvl)
                        item["lvl"] = lvl
                    over[ilvl] = item
                self.lfos.append((lsid, over))
        self.lfo_num = {}
        self.list_abs = {}

    def read_lvl(self, b, o, li):
        start = i32(b, o)
        nfc = b[o + 4] if o + 4 < len(b) else 0
        jc = (b[o + 5] & 3) if o + 5 < len(b) else 0
        nums = list(b[o + 6:o + 15])
        follow = b[o + 15] if o + 15 < len(b) else 0
        cbchp = b[o + 24] if o + 24 < len(b) else 0
        cbpap = b[o + 25] if o + 25 < len(b) else 0
        p = o + 28
        pap = b[p:p + cbpap]
        p += cbpap
        chp = b[p:p + cbchp]
        p += cbchp
        cch = u16(b, p)
        xst = b[p + 2:p + 2 + 2 * cch].decode("utf-16-le", "replace")
        p += 2 + 2 * cch
        pp = apply_pap({}, pap)
        rp = apply_chp({}, chp, None, self.fonts)
        fmt = NFC.get(nfc, "decimal")
        if fmt == "bullet":
            text = xst[:1] or "•"
        else:
            out = []
            for ch in xst:
                if ord(ch) < 9:
                    out.append("%%%d" % (ord(ch) + 1))
                else:
                    out.append(ch)
            text = "".join(out)
        ind = pp.get("ind_l", 720 * (li + 1))
        first = pp.get("ind_first", -360)
        lvl = {"start": start if start else (0 if nfc in (0,) and start == 0 else 1), "fmt": fmt, "text": text,
               "jc": {0: "left", 1: "center", 2: "right"}.get(jc, "left"), "ind": ind, "hang": max(0, -first)}
        if not start and fmt != "bullet":
            lvl["start"] = start
        if rp.get("font"):
            lvl["font"] = rp["font"]
        if follow == 2:
            lvl["text"] = text
        return lvl, p

    def num_for(self, ilfo):
        """The document model's list instance for a paragraph's list (1-based ilfo)."""
        if ilfo in self.lfo_num:
            return self.lfo_num[ilfo]
        if ilfo < 1 or ilfo > len(self.lfos) or ilfo == 2047:
            return None
        lsid, over = self.lfos[ilfo - 1]
        levels = self.lsts.get(lsid)
        if levels is None:
            return None
        restart = False
        if over:
            levels = [dict(l) for l in levels]
            for ilvl, item in over.items():
                if ilvl < 9:
                    if "lvl" in item:
                        levels[ilvl].update(item["lvl"])
                    if "start" in item:
                        levels[ilvl]["start"] = item["start"]
                        restart = True
            self.doc.lists.append(levels)
            ai = len(self.doc.lists) - 1
        else:
            if lsid not in self.list_abs:
                self.doc.lists.append(levels)
                self.list_abs[lsid] = len(self.doc.lists) - 1
            ai = self.list_abs[lsid]
        self.doc.nums.append((ai, restart))
        n = len(self.doc.nums) - 1
        self.lfo_num[ilfo] = n
        return n

    # ------------------------------------------------------------ plcs
    def plc(self, idx, cbdata):
        """(cps, data items) of a PLC in the table stream."""
        b = self.tbl_part(idx)
        if not b:
            return [], []
        n = (len(b) - 4) // (4 + cbdata) if cbdata else (len(b) // 4) - 1
        cps = [u32(b, 4 * k) for k in range(n + 1)]
        items = [b[4 * (n + 1) + cbdata * k:4 * (n + 1) + cbdata * (k + 1)] for k in range(n)]
        return cps, items

    def sttb(self, idx):
        b = self.tbl_part(idx)
        out = []
        if not b:
            return out
        ext = u16(b, 0) == 0xFFFF
        o = 2 if ext else 0
        n = u16(b, o)
        cbextra = u16(b, o + 2)
        o += 4
        for _ in range(n):
            if ext:
                cch = u16(b, o)
                s = b[o + 2:o + 2 + 2 * cch].decode("utf-16-le", "replace")
                o += 2 + 2 * cch
            else:
                cch = b[o] if o < len(b) else 0
                s = b[o + 1:o + 1 + cch].decode("cp1252", "replace")
                o += 1 + cch
            o += cbextra
            out.append(s)
        return out

    # ------------------------------------------------------------ pictures
    def picture(self, fc):
        d = self.data_stream
        if not d or fc + 0x44 > len(d):
            return None
        lcb = u32(d, fc)
        cbhdr = u16(d, fc + 4)
        mm = u16(d, fc + 6)
        dxa = i16(d, fc + 28)
        dya = i16(d, fc + 30)
        mx = u16(d, fc + 32) or 1000
        my = u16(d, fc + 34) or 1000
        p = fc + cbhdr
        if mm == 0x66:
            cch = d[p] if p < len(d) else 0
            p += 1 + cch
        end = fc + lcb
        blip = self.find_blip(d, p, end)
        if not blip:
            return None
        data, ext = blip
        w = max(1, dxa * mx // 1000)
        h = max(1, dya * my // 1000)
        return {"t": "image", "data": data, "ext": ext, "cx": w * B.EMU_PER_TWIP, "cy": h * B.EMU_PER_TWIP}

    def find_blip(self, d, p, end):
        """The first picture inside OfficeArt records between p and end: (bytes, ext)."""
        guard = 0
        while p + 8 <= end and guard < 2000:
            guard += 1
            ver_inst = u16(d, p)
            rt = u16(d, p + 2)
            ln = u32(d, p + 4)
            ver = ver_inst & 0xF
            inst = ver_inst >> 4
            body = p + 8
            if ver == 0xF and rt not in (0xF007,):
                # a container: look inside
                r = self.find_blip(d, body, min(end, body + ln))
                if r:
                    return r
            elif rt == 0xF007:
                # FBSE: the picture follows its 36-byte header (and name)
                cbname = u8(d, body + 33)
                r = self.find_blip(d, body + 36 + cbname, min(end, body + ln))
                if r:
                    return r
            elif 0xF018 <= rt <= 0xF117:
                return self.blip(d, p)
            p = body + ln
        return None

    def blip(self, d, p):
        ver_inst = u16(d, p)
        rt = u16(d, p + 2)
        ln = u32(d, p + 4)
        inst = ver_inst >> 4
        body = p + 8
        end = body + ln
        two_uids = inst in (0x3D5, 0x217, 0x6E1, 0x6E3, 0x7A9, 0x6E5, 0x46B, 0x2C5, 0x543)
        if rt in (0xF01A, 0xF01B, 0xF01C):
            o = body + (32 if inst in (0x3D5, 0x217, 0x543) else 16)
            comp = u8(d, o + 32)
            raw = d[o + 34:end]
            if comp == 0:
                try:
                    raw = zlib.decompress(raw)
                except zlib.error:
                    pass
            ext = {0xF01A: "emf", 0xF01B: "wmf", 0xF01C: "pict"}[rt]
            if ext == "wmf" and raw[:4] != b"\xd7\xcd\xc6\x9a":
                pass
            if ext == "pict":
                return None
            return raw, ext
        o = body + (32 if two_uids else 16) + 1
        raw = d[o:end]
        ext = {0xF01D: "jpg", 0xF02A: "jpg", 0xF01E: "png", 0xF01F: "bmp", 0xF029: "tif"}.get(rt)
        if ext == "bmp":
            # a DIB: give it a file header
            hdr = struct.pack("<2sIHHI", b"BM", 14 + len(raw), 0, 0, 14 + u32(raw, 0) + (
                4 * (u32(raw, 32) or (1 << u16(raw, 14))) if u16(raw, 14) <= 8 else 0))
            raw = hdr + raw
        if not ext:
            return None
        return raw, ext

    def read_drawings(self):
        """Floating pictures: shape id -> picture, from the drawing group."""
        self.shape_pics = {}
        self.shape_txbx = set()
        b = self.tbl_part(50)
        if not b:
            return
        bstore = []
        p = 0
        end = len(b)
        # OfficeArtDggContainer
        if u16(b, 2) == 0xF000:
            ln = u32(b, 4)
            q = 8
            qend = 8 + ln
            while q + 8 <= qend:
                rt = u16(b, q + 2)
                l2 = u32(b, q + 4)
                if rt == 0xF001:
                    r = q + 8
                    while r + 8 <= q + 8 + l2:
                        if u16(b, r + 2) == 0xF007:
                            body = r + 8
                            fo = u32(b, body + 28)
                            size = u32(b, body + 20)
                            cbname = u8(b, body + 33)
                            pic = None
                            if u32(b, r + 4) > 36 + cbname:
                                pic = self.find_blip(b, body + 36 + cbname, r + 8 + u32(b, r + 4))
                            elif fo != 0xFFFFFFFF and fo < len(self.wd):
                                pic = self.find_blip(self.wd, fo, fo + size)
                            bstore.append(pic)
                        r += 8 + u32(b, r + 4)
                q += 8 + l2
            p = qend
        # the drawings that follow: shapes and their picture index
        while p + 9 <= end:
            p += 1   # dgglbl
            if u16(b, p + 2) != 0xF002:
                break
            ln = u32(b, p + 4)
            self._walk_shapes(b, p + 8, p + 8 + ln, bstore)
            p += 8 + ln

    def _walk_shapes(self, b, p, end, bstore):
        while p + 8 <= end:
            vi = u16(b, p)
            rt = u16(b, p + 2)
            ln = u32(b, p + 4)
            if rt in (0xF003, 0xF004, 0xF002):
                if rt == 0xF004:
                    spid = None
                    pib = None
                    txid = None
                    q = p + 8
                    while q + 8 <= p + 8 + ln:
                        rt2 = u16(b, q + 2)
                        l2 = u32(b, q + 4)
                        if rt2 == 0xF00A:
                            spid = u32(b, q + 8)
                        elif rt2 == 0xF00B:
                            nprops = u16(b, q) >> 4
                            for k in range(nprops):
                                opid = u16(b, q + 8 + 6 * k)
                                val = u32(b, q + 10 + 6 * k)
                                pid = opid & 0x3FFF
                                if pid == 0x104:
                                    pib = val
                                elif pid == 0x80:
                                    txid = val
                        q += 8 + l2
                    if spid is not None:
                        if pib and 0 < pib <= len(bstore) and bstore[pib - 1]:
                            self.shape_pics[spid] = bstore[pib - 1]
                        if txid is not None:
                            self.shape_txbx.add(spid)
                else:
                    self._walk_shapes(b, p + 8, p + 8 + ln, bstore)
            p += 8 + ln

    # ------------------------------------------------------------ reading
    def read(self):
        self.read_pieces()
        self.read_grpprls()
        self.read_fkps()
        self.read_fonts()
        self.read_styles()
        self.build_styles()
        self.read_lists()
        try:
            self.read_drawings()
        except Exception:
            self.shape_pics = {}
            self.shape_txbx = set()
        self.read_meta()
        lw = self.lw
        ccp = {"text": lw[3] if len(lw) > 3 else len(self.text), "ftn": lw[4] if len(lw) > 4 else 0,
               "hdd": lw[5] if len(lw) > 5 else 0, "mcr": lw[6] if len(lw) > 6 else 0,
               "atn": lw[7] if len(lw) > 7 else 0, "edn": lw[8] if len(lw) > 8 else 0,
               "txbx": lw[9] if len(lw) > 9 else 0, "hdrtxbx": lw[10] if len(lw) > 10 else 0}
        base = 0
        self.story_base = {}
        for k in ("text", "ftn", "hdd", "mcr", "atn", "edn", "txbx", "hdrtxbx"):
            self.story_base[k] = base
            base += max(0, ccp[k])
        self.ccp = ccp
        self.read_notes()
        self.read_bookmarks()
        self.read_comments()
        self.read_spa()
        sections = self.read_sections()
        hdd = self.read_headers()
        self.txbx_stories = self.read_txbx()
        d = self.doc
        main = self.story_blocks(0, ccp["text"], top=True)
        # split the body at section ends
        for i, (cp_end, props) in enumerate(sections):
            s = B.section()
            s.update({k: v for k, v in props.items() if k in ("w", "h", "landscape", "cols", "col_space",
                                                             "title_pg", "break", "page_start")})
            s["margins"].update(props.get("margins", {}))
            for key in ("headers", "footers"):
                for typ, story in props.get(key, {}).items():
                    s[key][typ] = story
            d.sections.append(s)
        if not d.sections:
            d.sections.append(B.section())
        # blocks to sections by the section index each paragraph was tagged with
        for b in main:
            si = min(b.pop("_sect", 0), len(d.sections) - 1)
            d.sections[si]["blocks"].append(b)
        for si, s in enumerate(d.sections):
            hs = hdd.get(si, {})
            for typ, blocks in hs.get("headers", {}).items():
                s["headers"][typ] = blocks
            for typ, blocks in hs.get("footers", {}).items():
                s["footers"][typ] = blocks
            if not s["blocks"]:
                s["blocks"].append(B.para())
        return d

    def read_meta(self):
        si = self.cfb.stream("\x05SummaryInformation")
        if not si or len(si) < 48:
            return
        try:
            off = u32(si, 44)
            n = u32(si, off + 4)
            cp = 1252
            props = {}
            for k in range(n):
                pid = u32(si, off + 8 + 8 * k)
                po = off + u32(si, off + 12 + 8 * k)
                typ = u32(si, po)
                if typ == 2 and pid == 1:
                    cp = u16(si, po + 4)
                if typ == 30:
                    ln = u32(si, po + 4)
                    props[pid] = si[po + 8:po + 8 + ln]
                elif typ == 31:
                    ln = u32(si, po + 4)
                    props[pid] = si[po + 8:po + 8 + 2 * ln].decode("utf-16-le", "replace").rstrip("\x00")
            enc = "utf-8" if cp == 65001 else ("cp%d" % cp if cp and cp != 1200 else "cp1252")
            for pid, key in ((2, "title"), (3, "subject"), (4, "creator"), (5, "keywords"), (6, "description")):
                v = props.get(pid)
                if isinstance(v, bytes):
                    try:
                        v = v.decode(enc, "replace")
                    except LookupError:
                        v = v.decode("cp1252", "replace")
                    v = v.rstrip("\x00")
                if v:
                    self.doc.meta[key] = v
        except Exception:
            pass

    def read_notes(self):
        self.notes = {}
        for kind, ref, txt, story in (("footnote", 2, 3, "ftn"), ("endnote", 46, 47, "edn")):
            cps, items = self.plc(ref, 2)
            tcps, _ = self.plc(txt, 0)
            base = self.story_base[story]
            for k, cp in enumerate(cps[:-1]):
                if k + 1 < len(tcps):
                    self.notes[cp] = (kind, base + tcps[k], base + tcps[k + 1])

    def read_bookmarks(self):
        self.bm_start = {}
        self.bm_end = {}
        names = self.sttb(21)
        fcps, fitems = self.plc(22, 4)
        lcps, _ = self.plc(23, 0)
        for k, cp in enumerate(fcps[:-1]):
            if k >= len(names):
                break
            ibkl = u16(fitems[k], 0)
            name = names[k]
            if name.startswith("_") and name not in ("_Toc", ) and not name.startswith("_Toc") and not name.startswith("_Ref"):
                continue
            self.bm_start.setdefault(cp, []).append(name)
            if ibkl < len(lcps):
                self.bm_end.setdefault(lcps[ibkl], []).append(name)

    def read_comments(self):
        self.comments = {}
        cps, items = self.plc(4, 30)
        tcps, _ = self.plc(5, 0)
        owners = []
        b = self.tbl_part(36)
        o = 0
        while o + 2 <= len(b):
            cch = u16(b, o)
            owners.append(b[o + 2:o + 2 + 2 * cch].decode("utf-16-le", "replace"))
            o += 2 + 2 * cch
        base = self.story_base["atn"]
        for k, cp in enumerate(cps[:-1]):
            it = items[k]
            cch = u16(it, 0)
            initials = it[2:2 + 2 * min(cch, 9)].decode("utf-16-le", "replace")
            ibst = u16(it, 20)
            author = owners[ibst] if ibst < len(owners) else ""
            if k + 1 < len(tcps):
                self.comments[cp] = (author, initials, base + tcps[k], base + tcps[k + 1])

    def read_spa(self):
        self.spa = {}
        cps, items = self.plc(40, 26)
        for k, cp in enumerate(cps[:-1]):
            it = items[k]
            spid = u32(it, 0)
            xl, yt, xr, yb = i32(it, 4), i32(it, 8), i32(it, 12), i32(it, 16)
            fl = u16(it, 20)
            self.spa[cp] = (spid, xl, yt, xr, yb, fl)

    def read_txbx(self):
        cps, _ = self.plc(56, 22)
        base = self.story_base["txbx"]
        out = []
        for k in range(len(cps) - 2):
            a, b2 = base + cps[k], base + cps[k + 1]
            if b2 > a:
                out.append((a, b2))
        return out

    def read_sections(self):
        cps, items = self.plc(6, 12)
        out = []
        for k, cp in enumerate(cps[1:]):
            it = items[k]
            fc = u32(it, 2)
            props = {"w": 12240, "h": 15840, "margins": {"top": 1440, "bottom": 1440, "left": 1800,
                                                         "right": 1800, "header": 720, "footer": 720, "gutter": 0},
                     "break": "nextPage"}
            if fc != 0xFFFFFFFF and fc < len(self.wd):
                cb = u16(self.wd, fc)
                for op, a in sprms(self.wd[fc + 2:fc + 2 + cb]):
                    if op == 0xB01F:
                        props["w"] = u16(a, 0)
                    elif op == 0xB020:
                        props["h"] = u16(a, 0)
                    elif op == 0xB021:
                        props["margins"]["left"] = u16(a, 0)
                    elif op == 0xB022:
                        props["margins"]["right"] = u16(a, 0)
                    elif op == 0x9023:
                        props["margins"]["top"] = abs(i16(a, 0))
                    elif op == 0x9024:
                        props["margins"]["bottom"] = abs(i16(a, 0))
                    elif op == 0xB017:
                        props["margins"]["header"] = u16(a, 0)
                    elif op == 0xB018:
                        props["margins"]["footer"] = u16(a, 0)
                    elif op == 0xB025:
                        props["margins"]["gutter"] = u16(a, 0)
                    elif op == 0x500B:
                        props["cols"] = u16(a, 0) + 1
                    elif op == 0x900C:
                        props["col_space"] = u16(a, 0)
                    elif op == 0x3009:
                        props["break"] = {0: "continuous", 1: "nextColumn", 2: "nextPage", 3: "evenPage",
                                          4: "oddPage"}.get(u8(a, 0), "nextPage")
                    elif op == 0x300A:
                        props["title_pg"] = bool(u8(a, 0))
                    elif op == 0x301D:
                        props["landscape"] = u8(a, 0) == 2
                    elif op == 0x501C:
                        props["page_start"] = u16(a, 0)
            out.append((cp, props))
        self.section_ends = [cp for cp, _ in out]
        return out

    def read_headers(self):
        cps, _ = self.plc(11, 0)
        base = self.story_base["hdd"]
        out = {}
        if len(cps) < 8:
            return out
        stories = []
        for k in range(len(cps) - 1):
            stories.append((base + cps[k], base + cps[k + 1]))
        nsec = (len(stories) - 6) // 6
        prev = {}
        order = [("headers", "even"), ("headers", "default"), ("footers", "even"), ("footers", "default"),
                 ("headers", "first"), ("footers", "first")]
        for si in range(nsec):
            got = {"headers": {}, "footers": {}}
            for j, (key, typ) in enumerate(order):
                a, b2 = stories[6 + si * 6 + j]
                if b2 - a > 1:
                    blocks = self.story_blocks(a, b2 - 1)
                    prev[(key, typ)] = blocks
                if (key, typ) in prev:
                    got[key][typ] = prev[(key, typ)]
            out[si] = got
        return out

    # ------------------------------------------------------------ stories
    def story_blocks(self, cp0, cp1, top=False):
        """The blocks of the text between two character positions."""
        cp1 = min(cp1, len(self.text))
        units = self.paragraphs(cp0, cp1, top)
        blocks, _ = self.group(units, 0, 0)
        return blocks

    def paragraphs(self, cp0, cp1, top=False):
        """Paragraph units: dicts with runs, paragraph props, table markers."""
        text = self.text
        out = []
        cp = cp0
        ends = getattr(self, "section_ends", []) if top else []
        sect_marks = set(e - 1 for e in ends)
        self.fields = []
        import bisect
        while cp < cp1:
            # find the paragraph end (a section mark ends one too)
            e = cp
            while e < cp1 and text[e] not in "\r\x07" and not (text[e] == "\x0c" and e in sect_marks):
                e += 1
            end_char = text[e] if e < cp1 else "\r"
            unit = self.paragraph(cp, min(e, cp1), end_char)
            if top:
                unit["_sect"] = min(bisect.bisect_right(ends, e), max(0, len(ends) - 1))
            out.append(unit)
            cp = e + 1
        return out

    def paragraph(self, cp0, cp1, end_char):
        fc, comp, prm = self.fc_of(cp1 if cp1 < len(self.text) else max(0, cp1 - 1))
        papx = self.papx_at(fc) if fc is not None else None
        istd = papx[2] if papx else 0
        pp = {}
        if papx:
            apply_pap(pp, papx[3])
        if prm:
            apply_pap(pp, self.prm_sprms(prm))
        st_pp, st_rp = self.style_props(istd)
        sid = self.style_ids.get(istd, "Normal")
        if not self.doc.style(sid):
            sid = "Normal"
        ilfo = pp.pop("_ilfo", None)
        ilvl = pp.pop("_ilvl", st_pp.get("_ilvl", 0))
        if ilfo is None:
            ilfo = st_pp.get("_ilfo")
        if ilfo:
            n = self.num_for(ilfo)
            if n is not None:
                pp["num"] = (n, min(8, ilvl))
                # the list's indents unless the paragraph sets its own
                if "ind_l" not in pp:
                    pass
        elif ilfo == 0 and st_pp.get("_ilfo"):
            pp["num"] = (-1, 0)
        intable = pp.get("_intable", st_pp.get("_intable", False))
        itap = pp.get("_itap", 1 if intable else 0)
        if not intable and "_itap" not in pp:
            itap = 0
        p = {"style": sid, "ppr": {k: v for k, v in pp.items() if not k.startswith("_")}, "rpr": {},
             "runs": [], "_itap": itap, "_ttp": pp.get("_ttp", False) and itap <= 1,
             "_innerttp": pp.get("_innerttp", False), "_innercell": pp.get("_innercell", False),
             "_cellend": end_char == "\x07", "_tap": papx[3] if papx else b""}
        if p["_innerttp"]:
            p["_ttp"] = False
        self.runs(cp0, cp1, p["runs"], st_rp)
        # a field running on into the next paragraphs (a table of contents)
        if self.fields and self.fields[0]["state"] == "result" and len(self.fields) == 1:
            f = self.fields[0]
            p["runs"].append({"t": "fbegin", "instr": f["instr"].strip()})
            p["runs"].append({"t": "fsep"})
            p["runs"].extend(f["result"])
            f["result"] = []
            f["state"] = "pass"
        # the paragraph mark's own formatting
        mfc, _, _ = self.fc_of(cp1)
        if mfc is not None:
            ch = self.chpx_at(mfc)
            if ch and ch[2]:
                mr = apply_chp({}, ch[2], st_rp, self.fonts)
                p["rpr"] = {k: v for k, v in mr.items() if not k.startswith("_")}
        return p

    def runs(self, cp0, cp1, out, st_rp):
        text = self.text
        cp = cp0
        while cp < cp1:
            fc, comp, prm = self.fc_of(cp)
            if fc is None:
                break
            ch = self.chpx_at(fc)
            # run end: CHPX range end, piece end, or paragraph end
            run_end = cp1
            if ch:
                span = (ch[1] - fc) // (1 if comp else 2)
                run_end = min(run_end, cp + max(1, span))
            for cp0p, cp1p, _f, _c, _p in self.pieces:
                if cp0p <= cp < cp1p:
                    run_end = min(run_end, cp1p)
                    break
            r = {}
            istd_c = None
            if ch and ch[2]:
                apply_chp(r, ch[2], st_rp, self.fonts)
            if prm:
                apply_chp(r, self.prm_sprms(prm), st_rp, self.fonts)
            if "_istd" in r:
                istd_c = r.pop("_istd")
            cstyle = self.style_ids.get(istd_c) if istd_c not in (None, 10) else None
            if cstyle and self.doc.style(cstyle) and self.doc.style(cstyle)["type"] != "character":
                cstyle = None
            seg = text[cp:run_end]
            self.segment(cp, seg, r, cstyle, out)
            cp = run_end

    def segment(self, cp, seg, r, cstyle, out):
        clean = {k: v for k, v in r.items() if not k.startswith("_")}
        if r.get("_rmdel"):
            return
        buf = []
        pos = cp

        def flush():
            if buf:
                self.emit(out, {"t": "text", "text": "".join(buf), "rpr": dict(clean), "cstyle": cstyle})
                del buf[:]
        for i, c in enumerate(seg):
            here = cp + i
            if here in self.bm_start or here in self.bm_end:
                flush()
                for n in self.bm_end.get(here, []):
                    self.emit(out, {"t": "bmend", "name": n})
                for n in self.bm_start.get(here, []):
                    self.emit(out, {"t": "bmstart", "name": n})
            o = ord(c)
            if c == "\x13":
                flush()
                self.fields.append({"state": "code", "instr": "", "result": [], "rpr": clean})
                continue
            if c == "\x14":
                flush()
                if self.fields:
                    self.fields[-1]["state"] = "result"
                continue
            if c == "\x15":
                flush()
                if self.fields:
                    f = self.fields.pop()
                    self.close_field(f, out)
                continue
            if self.fields and self.fields[-1]["state"] == "code":
                if o >= 0x20 or c == "\t":
                    self.fields[-1]["instr"] += c
                continue
            if c == "\x07":
                continue
            if c == "\t":
                flush()
                self.emit(out, {"t": "tab", "rpr": dict(clean)})
            elif c == "\x0b":
                flush()
                self.emit(out, {"t": "br", "rpr": dict(clean)})
            elif c == "\x0c":
                flush()
                self.emit(out, {"t": "page", "rpr": dict(clean)})
            elif c == "\x0e":
                flush()
                self.emit(out, {"t": "col", "rpr": dict(clean)})
            elif c == "\x1e":
                buf.append("‑")
            elif c == "\x1f":
                buf.append("­")
            elif c == "\xa0":
                buf.append(" ")
            elif c in "\x01\x08" and r.get("_spec", False) or (c == "\x01" and "_pic" in r):
                flush()
                if c == "\x01" and "_pic" in r and not r.get("_ole"):
                    img = self.picture(r["_pic"])
                    if img:
                        self.emit(out, img)
                elif c == "\x08":
                    self.floating(here, out)
                elif c == "\x01" and r.get("_ole") and "_pic" in r:
                    img = self.picture(r["_pic"])
                    if img:
                        self.emit(out, img)
            elif c == "\x02" and r.get("_spec", True):
                flush()
                n = self.notes.get(here)
                if n is not None:
                    kind, a, b2 = n
                    saved = self.fields
                    blocks = self.story_blocks(a, max(a, b2 - 1))
                    self.fields = saved
                    if blocks and not blocks[0].get("table"):
                        rs = blocks[0]["runs"]
                        if rs and rs[0].get("t") == "text":
                            rs[0]["text"] = rs[0]["text"].lstrip(" ")
                    self.emit(out, {"t": "note", "kind": kind, "blocks": blocks, "rpr": {}})
            elif c == "\x05" and r.get("_spec", True):
                flush()
                cm = self.comments.get(here)
                if cm is not None:
                    author, initials, a, b2 = cm
                    saved = self.fields
                    blocks = self.story_blocks(a, max(a, b2 - 1))
                    self.fields = saved
                    for b in blocks:
                        if not b.get("table"):
                            b["style"] = "CommentText" if self.doc.style("CommentText") else b.get("style")
                    cid = len(self.doc.comments)
                    self.doc.comments.append({"id": cid, "author": author, "initials": initials, "date": "",
                                              "blocks": blocks})
                    self.emit(out, {"t": "cstart", "id": cid})
                    self.emit(out, {"t": "cend", "id": cid})
            elif o < 0x20 and c not in "\t":
                continue
            else:
                buf.append(c)
        flush()

    def emit(self, out, r):
        if self.fields and self.fields[-1]["state"] != "pass":
            f = self.fields[-1]
            if f["state"] == "code":
                return
            f["result"].append(r)
            return
        out.append(r)

    def close_field(self, f, out):
        if f["state"] == "pass":
            out.append({"t": "fend"})
            return
        instr = f["instr"].strip()
        word = instr.split(" ", 1)[0].upper() if instr else ""
        res = f["result"]
        if word == "HYPERLINK":
            import shlex
            try:
                parts = shlex.split(instr)
            except ValueError:
                parts = instr.split()
            url = None
            anchor = None
            k = 1
            while k < len(parts):
                if parts[k] == "\\l" and k + 1 < len(parts):
                    anchor = parts[k + 1]
                    k += 2
                    continue
                if not parts[k].startswith("\\") and url is None:
                    url = parts[k]
                k += 1
            r = {"t": "link", "url": url, "anchor": anchor if not url else None, "runs": res}
        elif word in ("EMBED", "SHAPE", "INCLUDEPICTURE", "IMPORT"):
            for x in res:
                self.emit(out, x)
            return
        else:
            r = {"t": "field", "instr": instr, "result": res, "rpr": f.get("rpr", {})}
        self.emit(out, r)

    def floating(self, cp, out):
        sp = self.spa.get(cp)
        if sp is None:
            return
        spid, xl, yt, xr, yb, fl = sp
        pic = self.shape_pics.get(spid)
        if pic:
            data, ext = pic
            w = max(1, xr - xl)
            h = max(1, yb - yt)
            bx = (fl >> 1) & 3
            by = (fl >> 3) & 3
            wr = (fl >> 5) & 0xF
            wrap = {0: "top", 1: "top", 2: "square", 3: "none", 4: "tight", 5: "tight"}.get(wr, "square")
            behind = bool(fl & 0x4000)
            self.emit(out, {"t": "image", "data": data, "ext": ext, "cx": w * B.EMU_PER_TWIP,
                            "cy": h * B.EMU_PER_TWIP,
                            "anchor": {"wrap": wrap, "behind": behind,
                                       "hrel": {0: "margin", 1: "page", 2: "column"}.get(bx, "column"),
                                       "vrel": {0: "margin", 1: "page", 2: "paragraph"}.get(by, "paragraph"),
                                       "x": xl * B.EMU_PER_TWIP, "y": yt * B.EMU_PER_TWIP}})
        elif spid in self.shape_txbx and self.txbx_stories:
            a, b2 = self.txbx_stories.pop(0)
            saved = self.fields
            self.fields = []
            blocks = self.story_blocks(a, max(a, b2 - 1))
            self.fields = saved
            self.__dict__.setdefault("pending_after", []).extend(blocks)

    # ------------------------------------------------------------ tables
    def group(self, units, i, depth):
        """Blocks from units[i:] at table depth `depth`; returns (blocks, next index)."""
        out = []
        n = len(units)
        while i < n:
            u = units[i]
            if u["_itap"] > depth:
                t, i = self.table(units, i, depth + 1)
                out.append(t)
                continue
            if u["_itap"] < depth:
                break
            out.append(self.block(u))
            i += 1
            pend = self.__dict__.pop("pending_after", None)
            if pend:
                out.extend(pend)
        return out, i

    def block(self, u):
        b = {k: v for k, v in u.items() if not k.startswith("_")}
        if "_sect" in u:
            b["_sect"] = u["_sect"]
        return b

    def table(self, units, i, depth):
        rows = []
        n = len(units)
        sect = units[i].get("_sect", 0)
        cur_row = []
        cur_cell = []
        while i < n:
            u = units[i]
            if u["_itap"] < depth:
                break
            if u["_itap"] > depth:
                t, i = self.table(units, i, depth + 1)
                cur_cell.append(t)
                continue
            is_row_end = u["_ttp"] if depth == 1 else u["_innerttp"]
            is_cell_end = u["_cellend"] if depth == 1 else u["_innercell"]
            if is_row_end:
                rows.append((cur_row, u["_tap"]))
                cur_row = []
                cur_cell = []
                i += 1
                # a table ends where the next paragraph isn't in it
                if i < n and units[i]["_itap"] < depth:
                    break
                continue
            cur_cell.append(self.block(u))
            pend = self.__dict__.pop("pending_after", None)
            if pend:
                cur_cell.extend(pend)
            if is_cell_end:
                cur_row.append(cur_cell)
                cur_cell = []
            i += 1
        if cur_cell:
            cur_row.append(cur_cell)
        if cur_row:
            rows.append((cur_row, b""))
        t = {"table": True, "rows": [], "cols": [], "borders": False, "_sect": sect}
        grid = set()
        row_specs = []
        for cells, tap in rows:
            spec = self.tap(tap)
            row_specs.append(spec)
            for x in spec.get("centers", []):
                grid.add(x)
        grid = sorted(grid)
        if len(grid) >= 2:
            t["cols"] = [max(1, grid[k + 1] - grid[k]) for k in range(len(grid) - 1)]
            left = grid[0]
            if left > 0:
                t["indent"] = left
        tb = None
        for (cells, tap), spec in zip(rows, row_specs):
            row = {"cells": []}
            if spec.get("header"):
                row["header"] = True
            if spec.get("height"):
                row["height"] = abs(spec["height"])
                row["exact"] = spec["height"] < 0
            if spec.get("cant_split"):
                row["cant_split"] = True
            if spec.get("jc"):
                t["align"] = spec["jc"]
            tb = tb or spec.get("tborders")
            centers = spec.get("centers") or []
            tcs = spec.get("tcs") or []
            for ci, blocks in enumerate(cells):
                for b in B.walk_blocks(blocks):
                    b.pop("_sect", None)
                c = {"blocks": blocks or [B.para()], "span": 1}
                if ci + 1 < len(centers) and len(grid) >= 2:
                    a, z = centers[ci], centers[ci + 1]
                    try:
                        c["span"] = max(1, grid.index(z) - grid.index(a))
                    except ValueError:
                        c["span"] = 1
                if ci < len(tcs):
                    tc = tcs[ci]
                    if tc.get("vmerge"):
                        c["vmerge"] = tc["vmerge"]
                    if tc.get("valign"):
                        c["valign"] = tc["valign"]
                    if tc.get("borders"):
                        c["borders"] = tc["borders"]
                    if tc.get("hmerge") == "cont":
                        c["_drop"] = True
                    elif tc.get("hmerge") == "first":
                        c["_hfirst"] = True
                shds = spec.get("shd") or []
                if ci < len(shds) and shds[ci]:
                    c["shd"] = shds[ci]
                row["cells"].append(c)
            # old-style horizontal merges: the merged cells join the first
            merged = []
            for c in row["cells"]:
                if c.pop("_drop", False) and merged:
                    merged[-1]["span"] += c["span"]
                    for b in c["blocks"]:
                        if b.get("runs") or b.get("table"):
                            merged[-1]["blocks"].append(b)
                else:
                    c.pop("_hfirst", None)
                    merged.append(c)
            row["cells"] = merged
            t["rows"].append(row)
        # cells left without borders get the table's
        if tb:
            t["tborders"] = tb
            for r in t["rows"]:
                for c in r["cells"]:
                    bd = c.setdefault("borders", {})
                    for side in ("top", "left", "bottom", "right"):
                        if side not in bd and tb.get(side):
                            bd[side] = tb[side]
        return t, i

    def tap(self, grpprl):
        spec = {}
        for op, a in sprms(grpprl):
            if op == 0xD608:
                nc = u8(a, 0)
                spec["centers"] = [i16(a, 1 + 2 * k) for k in range(nc + 1)]
                o = 1 + 2 * (nc + 1)
                tcs = []
                for k in range(nc):
                    if o + 20 > len(a):
                        tcs.append({})
                        continue
                    grf = u16(a, o)
                    tc = {}
                    if grf & 1:
                        tc["hmerge"] = "first"
                    if grf & 2:
                        tc["hmerge"] = "cont"
                    vm = (grf >> 5) & 3
                    if vm == 3:
                        tc["vmerge"] = "restart"
                    elif vm == 1:
                        tc["vmerge"] = "cont"
                    va = (grf >> 7) & 3
                    if va:
                        tc["valign"] = {1: "center", 2: "bottom"}.get(va)
                    bd = {}
                    for side, off in (("top", 4), ("left", 8), ("bottom", 12), ("right", 16)):
                        v = brc(a, o + off, False)
                        if v:
                            bd[side] = v
                    if bd:
                        tc["borders"] = bd
                    tcs.append(tc)
                    o += 20
                spec["tcs"] = tcs
            elif op in (0x5400, 0x548A):
                spec["jc"] = {1: "center", 2: "right"}.get(u16(a, 0))
            elif op == 0x9407:
                spec["height"] = i16(a, 0)
            elif op == 0x3404:
                spec["header"] = bool(u8(a, 0))
            elif op == 0x3403:
                spec["cant_split"] = bool(u8(a, 0))
            elif op == 0xD612 or op == 0xD616 or op == 0xD60C:
                shds = spec.setdefault("shd", [])
                start = {0xD612: 0, 0xD616: 22, 0xD60C: 44}[op]
                k = 0
                while 10 * k + 10 <= len(a):
                    idx = start + k
                    while len(shds) <= idx:
                        shds.append(None)
                    shds[idx] = shd(a, 10 * k, True)
                    k += 1
            elif op == 0xD609:
                shds = spec.setdefault("shd", [])
                k = 0
                while 2 * k + 2 <= len(a):
                    while len(shds) <= k:
                        shds.append(None)
                    if shds[k] is None:
                        shds[k] = shd(a, 2 * k, False)
                    k += 1
            elif op == 0xD613:
                tb = {}
                for k, side in enumerate(("top", "left", "bottom", "right", "insideH", "insideV")):
                    v = brc(a, 8 * k, True)
                    if v:
                        tb[side] = v
                spec["tborders"] = tb
            elif op == 0xD605:
                tb = {}
                for k, side in enumerate(("top", "left", "bottom", "right", "insideH", "insideV")):
                    v = brc(a, 4 * k, False)
                    if v:
                        tb[side] = v
                spec["tborders"] = spec.get("tborders") or tb
            elif op == 0xD62F or op == 0xD620:
                # sprmTSetBrc: borders of a range of cells
                ic0, ic1, sides = u8(a, 0), u8(a, 1), u8(a, 2)
                v = brc(a, 3, op == 0xD62F)
                for k in range(ic0, ic1):
                    tcs = spec.setdefault("tcs", [])
                    while len(tcs) <= k:
                        tcs.append({})
                    bd = tcs[k].setdefault("borders", {})
                    for bit, side in ((1, "top"), (2, "left"), (4, "bottom"), (8, "right")):
                        if sides & bit:
                            if v:
                                bd[side] = v
                            else:
                                bd.pop(side, None)
        return spec


def read(path):
    return Reader(path).read()
