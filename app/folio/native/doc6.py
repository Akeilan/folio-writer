"""Word 6.0 and Word 95 documents (.doc) read by Folio itself (W3-05).

The Word 6/95 binary format is Word 97's predecessor: the same stories, pieces, FKPs and
PLCs, but with a smaller FIB, no table stream, 8-bit text and names, one-byte sprm
opcodes, two-byte borders and numbering kept in each paragraph (ANLD) instead of list
tables. This reader translates those structures into their Word 97 equivalents and lets
the Word 97 reader (docread) build the document model from them."""
import struct

from . import docread as R
from .docread import u8, u16, i16, u32

# Word 6 sprm: (size, Word 97 opcode). size: 1/2/3/4/5/12 fixed, 0 none, -1 a length byte,
# -2 a two-byte length (sprmTDefTable), -3 sprmPChgTabs' own encoding.
S6 = {
    0: (0, None), 2: (2, 0x4600), 3: (-1, None), 4: (1, None), 5: (1, 0x2403), 6: (1, None), 7: (1, 0x2405),
    8: (1, 0x2406), 9: (1, 0x2407), 10: (1, None), 11: (1, None), 12: (-1, "anld"),
    13: (1, "nlvl"), 14: (1, 0x240C), 15: (-1, 0xC60D), 16: (2, 0x840E), 17: (2, 0x840F),
    18: (2, 0x4610), 19: (2, 0x8411), 20: (4, 0x6412), 21: (2, 0xA413), 22: (2, 0xA414),
    23: (-3, 0xC615), 24: (1, 0x2416), 25: (1, 0x2417), 26: (2, 0x8418), 27: (2, 0x8419),
    28: (2, 0x841A), 29: (1, 0x261B), 30: (2, None), 31: (2, None), 32: (2, None), 33: (2, None),
    34: (2, None), 35: (2, None), 36: (2, None), 37: (1, 0x2423), 38: (2, "brc:0x6424"),
    39: (2, "brc:0x6425"), 40: (2, "brc:0x6426"), 41: (2, "brc:0x6427"), 42: (2, "brc:0x6428"),
    43: (2, "brc:0x6629"), 44: (1, 0x242A), 45: (2, 0x442B), 46: (2, 0x442C), 47: (2, 0x442D),
    48: (2, 0x842E), 49: (2, 0x842F), 50: (1, 0x2430), 51: (1, 0x2431), 52: (-1, None),
    53: (1, None), 54: (1, None), 55: (1, None), 56: (1, None), 57: (1, None), 58: (1, None),
    59: (1, None), 60: (1, None), 61: (1, None), 62: (1, None), 63: (1, None), 64: (1, None),
    65: (1, 0x0800), 66: (1, 0x0801), 67: (1, 0x0802), 68: (-1, "pic"), 69: (2, 0x4804),
    70: (4, 0x6805), 71: (1, 0x0806), 72: (2, None), 73: (3, None), 74: (-1, None),
    75: (1, 0x080A), 76: (1, None), 77: (1, None), 78: (1, None), 79: (1, None),
    80: (2, 0x4A30), 81: (-1, None), 82: (0, None), 83: (0, None), 84: (1, None),
    85: (1, 0x0835), 86: (1, 0x0836), 87: (1, 0x0837), 88: (1, 0x0838), 89: (1, 0x0839),
    90: (1, 0x083A), 91: (1, 0x083B), 92: (1, 0x083C), 93: (2, "ftc"), 94: (1, 0x2A3E),
    95: (3, None), 96: (2, 0x8840), 97: (2, 0x4A41), 98: (1, 0x2A42), 99: (2, 0x4A43),
    100: (1, None), 101: (2, 0x4845), 102: (1, None), 103: (-1, None), 104: (1, 0x2A48),
    105: (-1, None), 106: (-1, None), 107: (2, 0x484B), 108: (-1, None), 109: (2, None),
    110: (2, None), 117: (1, 0x0855), 118: (1, 0x0856),
    119: (1, None), 120: (-1, None), 121: (2, None), 122: (2, None), 123: (2, None), 124: (2, None),
    131: (1, 0x3000), 132: (1, 0x3001), 133: (-1, None), 134: (1, None), 135: (1, None),
    136: (3, 0xF203), 137: (3, 0xF204), 138: (1, 0x3005), 139: (1, 0x3006), 140: (2, 0x5007),
    141: (2, 0x5008), 142: (1, 0x3009), 143: (1, 0x300A), 144: (2, 0x500B), 145: (2, 0x900C),
    146: (1, 0x300D), 147: (1, 0x300E), 148: (2, 0xB00F), 149: (2, 0xB010), 150: (1, 0x3011),
    151: (1, 0x3012), 152: (1, 0x3013), 153: (1, 0x3014), 154: (2, 0x5015), 155: (2, 0x9016),
    156: (2, 0xB017), 157: (2, 0xB018), 158: (1, 0x3019), 159: (1, 0x301A), 160: (2, 0x501B),
    161: (2, 0x501C), 162: (1, 0x301D), 163: (1, None), 164: (2, 0xB01F), 165: (2, 0xB020),
    166: (2, 0xB021), 167: (2, 0xB022), 168: (2, 0x9023), 169: (2, 0x9024), 170: (2, 0xB025),
    171: (2, 0x5026),
    182: (2, 0x5400), 183: (2, 0x9601), 184: (2, 0x9602), 185: (1, 0x3403), 186: (1, 0x3404),
    187: (12, "tborders"), 188: (-1, None), 189: (2, 0x9407), 190: (-2, "deftable"),
    191: (-1, None), 192: (4, 0x740A), 193: (5, None), 194: (4, 0x7621), 195: (2, 0x5622),
    196: (4, 0x7623), 197: (2, 0x5624), 198: (2, 0x5625), 199: (5, None), 200: (4, None),
}

# the code page of 8-bit text, by the document's language
LID_CP = {0x0405: 1250, 0x040E: 1250, 0x0415: 1250, 0x0418: 1250, 0x041A: 1250, 0x041B: 1250,
          0x0424: 1250, 0x0402: 1251, 0x0419: 1251, 0x0422: 1251, 0x0423: 1251, 0x0C1A: 1251,
          0x0408: 1253, 0x041F: 1254, 0x040D: 1255, 0x0401: 1256, 0x0425: 1257, 0x0426: 1257,
          0x0427: 1257, 0x042A: 1258, 0x041E: 874, 0x0411: 932, 0x0804: 936, 0x0412: 949,
          0x0404: 950}


def split6(grpprl):
    """(opcode, operand) of a Word 6 grpprl."""
    i, n = 0, len(grpprl)
    while i < n:
        op = grpprl[i]
        i += 1
        size, _ = S6.get(op, (None, None))
        if size is None:
            return                          # unknown: stop rather than misread the rest
        if size == -1:
            if i >= n:
                return
            size = grpprl[i]
            i += 1
        elif size == -2:
            if i + 2 > n:
                return
            size = u16(grpprl, i) - 1
            i += 2
            yield op, grpprl[i:i + size]
            i += size
            continue
        elif size == -3:
            size = grpprl[i] if i < n else 0
            if size == 255:
                dmax = u8(grpprl, i + 1)
                amax = u8(grpprl, i + 2 + dmax * 4)
                size = 1 + dmax * 4 + 1 + amax * 3
            i += 1
        yield op, grpprl[i:i + size]
        i += size


def brc6(v):
    """A Word 6 two-byte border as a Word 97 BRC80."""
    w = v & 7
    kind = (v >> 3) & 3
    ico = (v >> 6) & 0x1F
    space = (v >> 11) & 0x1F
    shadow = (v >> 5) & 1
    if not v:
        return b"\x00\x00\x00\x00"
    if w == 6:
        kind97, dpt = 6, 2          # dotted
    elif w == 7:
        kind97, dpt = 7, 2          # dashed
    else:
        kind97, dpt = {0: 0, 1: 1, 2: 2, 3: 3}.get(kind, 1), max(1, w) * 6
        if kind == 2:
            dpt = max(dpt, 12)
    if kind97 == 0:
        kind97 = 1
    return struct.pack("<BBBB", min(255, dpt), kind97, ico, space | (shadow << 5))


class Translator:
    """Word 6 grpprls rewritten as Word 97 ones; numbering (ANLD) becomes lists."""

    def __init__(self):
        self.anlds = {}       # key: ilfo
        self.lists = []       # (key, levels)

    def anld_list(self, a, nlvl):
        nfc = u8(a, 0)
        before = u8(a, 1)
        after = u8(a, 2)
        jc = u8(a, 3) & 3
        ftc = u16(a, 6)
        start = u16(a, 10)
        indent = i16(a, 12)
        chars = a[20:52]
        tb = chars[:before]
        ta = chars[before:before + after]
        key = (nfc, tb, ta, jc, ftc, start, indent, nlvl if 1 <= nlvl <= 9 else 0)
        if key not in self.anlds:
            self.lists.append(key)
            self.anlds[key] = len(self.lists)       # ilfo, 1-based
        return self.anlds[key]

    def pap(self, grpprl, with_istd=False):
        out = []
        anld = None
        nlvl = None
        for op, a in split6(grpprl):
            size, tgt = S6.get(op, (None, None))
            if tgt is None:
                continue
            if tgt == "anld":
                anld = a
            elif tgt == "nlvl":
                nlvl = u8(a, 0)
            elif isinstance(tgt, str) and tgt.startswith("brc:"):
                out.append(struct.pack("<H", int(tgt[4:], 16)) + brc6(u16(a, 0)))
            elif tgt == "tborders":
                out.append(struct.pack("<HB", 0xD605, 24) + b"".join(brc6(u16(a, 2 * k)) for k in range(6)))
            elif tgt == "deftable":
                out.append(self.deftable(a))
            else:
                out.append(self.encode(tgt, a))
        if anld is not None and len(anld) >= 52 and nlvl not in (0,):
            lv = nlvl if nlvl is not None else 10
            ilfo = self.anld_list(anld, lv)
            out.append(struct.pack("<HH", 0x460B, ilfo))
            out.append(struct.pack("<HB", 0x260A, (lv - 1) if 1 <= lv <= 9 else 0))
        elif nlvl == 0:
            out.append(struct.pack("<HH", 0x460B, 0))
        return b"".join(out)

    def chp(self, grpprl, fonts_map=None):
        out = []
        for op, a in split6(grpprl):
            size, tgt = S6.get(op, (None, None))
            if tgt is None:
                continue
            if tgt == "ftc":
                out.append(struct.pack("<H", 0x4A4F) + a[:2])
                out.append(struct.pack("<H", 0x4A51) + a[:2])
            elif tgt == "pic":
                out.append(struct.pack("<H", 0x6A03) + a[:4].ljust(4, b"\x00"))
            elif isinstance(tgt, int):
                out.append(self.encode(tgt, a))
        return b"".join(out)

    def sep(self, grpprl):
        return b"".join(self.encode(tgt, a) for op, a in split6(grpprl)
                        for tgt in [S6.get(op, (None, None))[1]] if isinstance(tgt, int))

    @staticmethod
    def encode(op, a):
        spra = op >> 13
        fixed = {0: 1, 1: 1, 2: 2, 3: 4, 4: 2, 5: 2, 7: 3}.get(spra)
        if fixed is not None:
            return struct.pack("<H", op) + a[:fixed].ljust(fixed, b"\x00")
        if op == 0xC615:
            return struct.pack("<H", op) + struct.pack("<B", len(a)) + a
        return struct.pack("<HB", op, min(255, len(a))) + a[:255]

    @staticmethod
    def deftable(a):
        nc = u8(a, 0)
        centers = a[1:1 + 2 * (nc + 1)]
        tcs = a[1 + 2 * (nc + 1):]
        out = bytearray(struct.pack("<B", nc) + centers)
        for k in range(nc):
            tc = tcs[10 * k:10 * k + 10]
            if len(tc) < 10:
                out += b"\x00" * 20
                continue
            rgf = u16(tc, 0) & 0x0003
            out += struct.pack("<HH", rgf, 0) + b"".join(brc6(u16(tc, 2 + 2 * s)) for s in range(4))
        return struct.pack("<HH", 0xD608, len(out) + 1) + bytes(out)


class Reader95(R.Reader):
    def __init__(self, path, cfb, wd):
        self.cfb = cfb
        self.wd = wd
        self.nfib = u16(wd, 2)
        flags = u16(wd, 0x0A)
        if flags & 0x0100:
            raise R.Unsupported("encrypted")
        self.flags = flags
        self.complex = bool(flags & 0x0004)
        self.ext_char = bool(flags & 0x1000)
        lid = u16(wd, 6)
        self.codepage = "cp%d" % LID_CP.get(lid, 1252)
        self.tbl = wd                       # no table stream: everything is in WordDocument
        self.data_stream = wd
        fcmin, fcmac = u32(wd, 0x18), u32(wd, 0x1C)
        self.fcmin, self.fcmac = fcmin, fcmac
        ccp = [struct.unpack_from("<i", wd, 0x34 + 4 * k)[0] for k in range(8)]
        # the Word 97 reader's FIB views: lw[3..10] = ccp, fclcb = the fc/lcb pairs
        self.lw = [u32(wd, 0x20), 0, 0] + ccp
        self.fclcb = [(u32(wd, 0x58 + 8 * k), u32(wd, 0x5C + 8 * k)) for k in range(38)]
        self.pn_first = (u16(wd, 0x18A), u16(wd, 0x18C))
        self.cpn_bte = (u16(wd, 0x18E), u16(wd, 0x190))
        self.tr = Translator()
        self.doc = R.B.Doc()

    # -------------------------------------------------------------- text
    def decode(self, raw):
        try:
            return raw.decode(self.codepage, "replace")
        except LookupError:
            return raw.decode("cp1252", "replace")

    def read_pieces(self):
        self.pieces = []
        clx = self.tbl_part(33) if self.complex else b""
        i = 0
        while i < len(clx):
            t = clx[i]
            if t == 1:
                i += 3 + u16(clx, i + 1)
            elif t == 2:
                lcb = u32(clx, i + 1)
                plc = clx[i + 5:i + 5 + lcb]
                n = (lcb - 4) // 12
                cps = [u32(plc, 4 * k) for k in range(n + 1)]
                for k in range(n):
                    pcd = 4 * (n + 1) + 8 * k
                    fc = u32(plc, pcd + 2)
                    prm = u16(plc, pcd + 6)
                    comp = True
                    if self.ext_char:
                        # Far East Word 95: pieces are Unicode unless marked compressed
                        comp = bool(fc & 0x40000000)
                        if comp:
                            fc = (fc & ~0x40000000) // 2
                    self.pieces.append((cps[k], cps[k + 1], fc, comp, prm))
                break
            else:
                break
        if not self.pieces:
            n = self.fcmac - self.fcmin
            self.pieces.append((0, n, self.fcmin, True, 0))
        chars = []
        for cp0, cp1, fc, comp, prm in self.pieces:
            n = cp1 - cp0
            if comp:
                raw = self.wd[fc:fc + n]
                # one character per byte for now: each run's font says its code page (see read)
                txt = raw.decode("latin-1") if not self.ext_char else self.decode(raw)
                chars.append(txt.ljust(n, "\x00")[:n])
            else:
                raw = self.wd[fc:fc + 2 * n]
                chars.append("".join(map(chr, struct.unpack("<%dH" % (len(raw) // 2), raw[:len(raw) // 2 * 2]))))
        self.text = "".join(chars)

    def read_grpprls(self):
        self.grpprls = []
        clx = self.tbl_part(33) if self.complex else b""
        i = 0
        while i < len(clx) and clx[i] == 1:
            cb = u16(clx, i + 1)
            g = clx[i + 3:i + 3 + cb]
            self.grpprls.append(self.tr.pap(g) + self.tr.chp(g))
            i += 3 + cb

    def prm_sprms(self, prm):
        if not prm:
            return b""
        if prm & 1:
            i = prm >> 1
            return self.grpprls[i] if i < len(self.grpprls) else b""
        op = (prm >> 1) & 0x7F
        val = prm >> 8
        g = bytes([op, val & 0xFF])
        return self.tr.pap(g) + self.tr.chp(g)

    # -------------------------------------------------------------- FKPs
    def _bte_pns(self, idx, which):
        plc = self.tbl_part(idx)
        n = (len(plc) - 4) // 6 if plc else 0
        pns = [u16(plc, 4 * (n + 1) + 2 * k) for k in range(n)]
        # a non-complex file can leave out BTEs that follow on consecutive pages
        want = self.cpn_bte[which]
        while pns and len(pns) < want:
            pns.append(pns[-1] + 1)
        return pns

    def read_fkps(self):
        self.chpx_runs = []
        for pn in self._bte_pns(12, 0):
            page = self.wd[pn * 512:pn * 512 + 512]
            if len(page) < 512:
                continue
            crun = page[511]
            for j in range(crun):
                fc0, fc1 = u32(page, 4 * j), u32(page, 4 * (j + 1))
                off = page[4 * (crun + 1) + j] * 2
                g = page[off + 1:off + 1 + page[off]] if off else b""
                self.chpx_runs.append((fc0, fc1, self.tr.chp(g)))
        self.chpx_runs.sort(key=lambda x: x[0])
        self.papx_runs = []
        for pn in self._bte_pns(13, 1):
            page = self.wd[pn * 512:pn * 512 + 512]
            if len(page) < 512:
                continue
            cpara = page[511]
            for j in range(cpara):
                fc0, fc1 = u32(page, 4 * j), u32(page, 4 * (j + 1))
                off = page[4 * (cpara + 1) + 7 * j] * 2       # BX: offset and a 6-byte PHE
                if not off:
                    self.papx_runs.append((fc0, fc1, 0, b""))
                    continue
                cw = page[off]
                body = page[off + 1:off + 1 + 2 * cw]
                istd = body[0] if body else 0
                self.papx_runs.append((fc0, fc1, istd, self.tr.pap(body[1:])))
        self.papx_runs.sort(key=lambda x: x[0])
        import bisect
        self._chpx_starts = [r[0] for r in self.chpx_runs]
        self._papx_starts = [r[0] for r in self.papx_runs]
        self._bisect = bisect

    # -------------------------------------------------------------- fonts, styles
    def read_fonts(self):
        b = self.tbl_part(15)
        self.fonts = []
        self.font_cp = {}
        if len(b) < 2:
            return
        end = min(len(b), u16(b, 0))
        o = 2
        while o < end:
            cb = b[o] + 1
            ffn = b[o:o + cb]
            name = self.decode(ffn[6:].split(b"\x00")[0]) or "Times New Roman"
            self.fonts.append(name)
            chs = ffn[4] if len(ffn) > 4 else 0
            cp = CHARSET_CP.get(chs)
            for suffix, c in ((" Cyr", 1251), (" CE", 1250), (" Greek", 1253), (" Tur", 1254),
                              (" Baltic", 1257)):
                if name.endswith(suffix):
                    cp = c
            if self.font_cp.get(name) in (None, 1252):
                self.font_cp[name] = cp
            o += cb

    def read_styles(self):
        b = self.tbl_part(1)
        self.styles = {}
        self.raw_styles = {}
        if not b:
            return
        cbstshi = u16(b, 0)
        stshi = b[2:2 + cbstshi]
        cstd = u16(stshi, 0)
        cbbase = u16(stshi, 2)
        ftc = u16(stshi, 12) if len(stshi) >= 14 else 0
        self.default_ftc = [ftc, ftc, ftc]
        o = 2 + cbstshi
        raw = {}
        for istd in range(cstd):
            if o + 2 > len(b):
                break
            cb = u16(b, o)
            std = b[o + 2:o + 2 + cb]
            o += 2 + cb
            if not cb or len(std) < cbbase:
                continue
            sti = u16(std, 0) & 0x0FFF
            w2 = u16(std, 2)
            sgc = w2 & 0x0F
            base = w2 >> 4
            w3 = u16(std, 4)
            cupx = w3 & 0x0F
            nxt = w3 >> 4
            p = cbbase
            cch = std[p] if p < len(std) else 0
            name = self.decode(std[p + 1:p + 1 + cch])
            p += 1 + cch + 1
            upx = []
            for _ in range(cupx):
                if p % 2:
                    p += 1
                cbu = u16(std, p)
                upx.append(std[p + 2:p + 2 + cbu])
                p += 2 + cbu
            # into Word 97's shape: a paragraph style's UPX starts with its istd
            if sgc == 1 and len(upx) >= 2:
                outline = struct.pack("<HB", 0x2640, sti - 1) if 1 <= sti <= 9 else b""
                upx = [upx[0][:2] + self.tr.pap(upx[0][2:]) + outline, self.tr.chp(upx[1])]
            elif sgc == 2 and upx:
                upx = [self.tr.chp(upx[0])]
            name = name or STI_NAMES.get(sti, "")
            raw[istd] = {"sti": sti, "stk": sgc, "base": base if base != 0xFFF else None,
                         "next": nxt if nxt != 0xFFF else None, "name": name, "upx": upx}
        self.raw_styles = raw

    # -------------------------------------------------------------- lists from numbering
    def read_lists(self):
        self.lsts = {}
        self.lfos = []
        self.lfo_num = {}
        self.list_abs = {}
        for key in self.tr.lists:
            nfc, tb, ta, jc, ftc, start, indent, lvl = key
            fmt = R.NFC.get(nfc, "decimal")
            if nfc in (23, 0xFF) or (fmt == "bullet"):
                fmt = "bullet"
            tb_s = self.decode(tb)
            ta_s = self.decode(ta)
            if fmt == "bullet":
                text = tb_s[:1] or "•"
                if ftc < len(self.fonts) and self.fonts[ftc].lower() == "symbol" and text == "\xb7":
                    text = "•"
                    ftc = None
            else:
                text = tb_s + "%%%d" % (max(1, lvl) if lvl else 1) + ta_s
            ind = abs(indent) or 360
            levels = []
            for li in range(9):
                lv = {"start": start or 1, "fmt": fmt if (li == (lvl - 1 if lvl else 0)) else "decimal",
                      "text": text if li == (lvl - 1 if lvl else 0) else "%%%d." % (li + 1),
                      "jc": {0: "left", 1: "center", 2: "right"}.get(jc, "left"),
                      "ind": ind * (li + 1), "hang": ind}
                if ftc is not None and ftc < len(self.fonts) and fmt == "bullet":
                    lv["font"] = self.fonts[ftc]
                levels.append(lv)
            lsid = len(self.lfos) + 1
            self.lsts[lsid] = levels
            self.lfos.append((lsid, {}))

    def read_drawings(self):
        self.shape_pics = {}
        self.shape_txbx = set()

    # -------------------------------------------------------------- plcs and tables
    def sttb(self, idx):
        b = self.tbl_part(idx)
        out = []
        if len(b) < 2:
            return out
        end = min(len(b), u16(b, 0))
        o = 2
        while o < end:
            cch = b[o]
            out.append(self.decode(b[o + 1:o + 1 + cch]))
            o += 1 + cch
        return out

    def read_comments(self):
        self.comments = {}
        cps, items = self.plc(4, 20)
        tcps, _ = self.plc(5, 0)
        owners = []
        b = self.tbl_part(36)
        o = 0
        while o < len(b):
            cch = b[o]
            owners.append(self.decode(b[o + 1:o + 1 + cch]))
            o += 1 + cch
        base = self.story_base["atn"]
        for k, cp in enumerate(cps[:-1]):
            it = items[k]
            cch = min(9, it[0]) if it else 0
            initials = self.decode(it[1:1 + cch])
            ibst = u16(it, 10) if len(it) >= 12 else 0
            author = owners[ibst] if ibst < len(owners) else ""
            if k + 1 < len(tcps):
                self.comments[cp] = (author, initials, base + tcps[k], base + tcps[k + 1])

    def read(self):
        d = super().read()
        if not self.ext_char:
            self.recode(d)
        return d

    def recode(self, d):
        """The 8-bit text of each run in the code page of its font's character set."""
        styles = {st["id"]: st for st in d.styles}
        base_font = (d.defaults.get("rpr") or {}).get("font")

        def style_font(sid, depth=0):
            st = styles.get(sid)
            if not st or depth > 20:
                return base_font
            return (st.get("rpr") or {}).get("font") or style_font(st.get("based"), depth + 1)

        tag_cp = {}
        for lid, tag in R.LID_TAG.items():
            if lid in LID_CP:
                tag_cp[tag] = LID_CP[lid]

        def fix(text, font, lang=None):
            cp = self.font_cp.get(font) if font else None
            if cp == 1252 or cp is None:
                # an ANSI font shows the code page of the text's language (or the document's)
                cp = tag_cp.get(lang) or int(self.codepage[2:])
            if cp == "symbol":
                return text
            enc = ("cp%d" % cp) if cp else self.codepage
            try:
                return text.encode("latin-1").decode(enc, "replace")
            except (UnicodeEncodeError, LookupError):
                return text

        def runs(rs, pfont):
            for r in rs:
                f = (r.get("rpr") or {}).get("font") or (style_font(r["cstyle"]) if r.get("cstyle") else None) or pfont
                if r.get("t") == "text":
                    r["text"] = fix(r.get("text", ""), f, (r.get("rpr") or {}).get("lang"))
                elif r.get("t") == "link":
                    runs(r.get("runs") or [], pfont)
                elif r.get("t") == "field":
                    r["instr"] = fix(r.get("instr", ""), f)
                    if isinstance(r.get("result"), list):
                        runs(r["result"], pfont)
                elif r.get("t") == "fbegin":
                    r["instr"] = fix(r.get("instr", ""), f)
                elif r.get("t") == "note":
                    blocks(r.get("blocks") or [])

        def blocks(bs):
            for b in bs:
                if b.get("table"):
                    for row in b["rows"]:
                        for c in row["cells"]:
                            blocks(c.get("blocks") or [])
                else:
                    pf = (b.get("rpr") or {}).get("font") or style_font(b.get("style"))
                    runs(b.get("runs") or [], pf)
        for sec in d.sections:
            blocks(sec["blocks"])
            for key in ("headers", "footers"):
                for bl in (sec.get(key) or {}).values():
                    blocks(bl or [])
        for c in d.comments:
            blocks(c.get("blocks") or [])

    def read_spa(self):
        self.spa = {}

    def read_txbx(self):
        return []

    def sepx_grpprl(self, fc):
        cb = u16(self.wd, fc)
        return self.tr.sep(self.wd[fc + 2:fc + 2 + cb])

    def read_sections(self):
        out = super().read_sections()
        # which header and footer stories each section has (Word 6 keeps only those)
        cps, items = self.plc(6, 12)
        self.sect_ihdt = []
        for k in range(len(cps) - 1):
            fc = u32(items[k], 2)
            bits = 0
            if fc != 0xFFFFFFFF and fc + 2 <= len(self.wd):
                cb = u16(self.wd, fc)
                for op, a in split6(self.wd[fc + 2:fc + 2 + cb]):
                    if op == 153:
                        bits = u8(a, 0)
            self.sect_ihdt.append(bits)
        return out

    def read_headers(self):
        cps, _ = self.plc(11, 0)
        base = self.story_base["hdd"]
        out = {}
        if len(cps) < 2:
            return out
        stories = [(base + cps[k], base + cps[k + 1]) for k in range(len(cps) - 1)]
        per = [bin(b & 0x3F).count("1") for b in self.sect_ihdt]
        dop = self.tbl_part(31)
        nsep = bin(dop[1]).count("1") if len(dop) > 1 else 0
        if nsep + sum(per) > len(stories):
            nsep = max(0, len(stories) - sum(per))
        order = [("headers", "even"), ("headers", "default"), ("footers", "even"), ("footers", "default"),
                 ("headers", "first"), ("footers", "first")]
        k = nsep
        prev = {}
        for si, bits in enumerate(self.sect_ihdt):
            got = {"headers": {}, "footers": {}}
            for j, (key, typ) in enumerate(order):
                if bits & (1 << j) and k < len(stories):
                    a, b2 = stories[k]
                    k += 1
                    prev[(key, typ)] = self.story_blocks(a, b2 - 1) if b2 - a > 1 else None
                if prev.get((key, typ)):
                    got[key][typ] = prev[(key, typ)]
            out[si] = got
        return out

    # -------------------------------------------------------------- pictures
    def picture(self, fc):
        d = self.wd
        if fc + 0x44 > len(d):
            return None
        lcb = u32(d, fc)
        cbhdr = u16(d, fc + 4)
        mm = u16(d, fc + 6)
        dxa, dya = i16(d, fc + 28), i16(d, fc + 30)
        mx, my = u16(d, fc + 32) or 1000, u16(d, fc + 34) or 1000
        raw = d[fc + cbhdr:fc + lcb]
        if mm in (0x64, 0x66):
            return super().picture(fc)
        if mm == 99 and raw:
            # a device-independent bitmap
            bits = u16(raw, 14) if len(raw) > 16 else 24
            ncol = u32(raw, 32) if len(raw) > 36 else 0
            pal = 4 * (ncol or (1 << bits)) if bits <= 8 else 0
            raw = struct.pack("<2sIHHI", b"BM", 14 + len(raw), 0, 0, 14 + u32(raw, 0) + pal) + raw
            ext = "bmp"
        elif raw[:4] == b"\xd7\xcd\xc6\x9a":
            ext = "wmf"
        elif len(raw) >= 18 and u16(raw, 0) in (1, 2) and u16(raw, 2) == 9:
            # a metafile: give it the placeable header picture readers expect
            hdr = struct.pack("<IHhhhhHI", 0x9AC6CDD7, 0, 0, 0, max(1, dxa), max(1, dya), 1440, 0)
            chk = 0
            for k in range(10):
                chk ^= u16(hdr, 2 * k)
            raw = hdr + struct.pack("<H", chk) + raw
            ext = "wmf"
        else:
            return None
        w = max(1, dxa * mx // 1000)
        h = max(1, dya * my // 1000)
        return {"t": "image", "data": raw, "ext": ext, "cx": w * R.B.EMU_PER_TWIP, "cy": h * R.B.EMU_PER_TWIP}


CHARSET_CP = {0: 1252, 1: None, 2: "symbol", 77: None, 128: 932, 129: 949, 130: 1361, 134: 936,
              136: 950, 161: 1253, 162: 1254, 163: 1258, 177: 1255, 178: 1256, 186: 1257,
              204: 1251, 222: 874, 238: 1250, 255: 437}

# names of Word's built-in styles when a Word 6 file leaves them out
STI_NAMES = {0: "Normal", 1: "heading 1", 2: "heading 2", 3: "heading 3", 4: "heading 4",
             5: "heading 5", 6: "heading 6", 7: "heading 7", 8: "heading 8", 9: "heading 9",
             10: "index 1", 19: "toc 1", 20: "toc 2", 21: "toc 3", 22: "toc 4", 23: "toc 5",
             24: "toc 6", 25: "toc 7", 26: "toc 8", 27: "toc 9", 28: "Normal Indent",
             29: "footnote text", 30: "annotation text", 31: "header", 32: "footer",
             34: "caption", 37: "envelope address", 38: "footnote reference",
             39: "annotation reference", 42: "endnote reference", 43: "endnote text",
             47: "List", 48: "List Bullet", 49: "List Number", 62: "Title", 63: "Closing",
             64: "Signature", 65: "Default Paragraph Font", 66: "Body Text",
             74: "Subtitle", 90: "Plain Text"}
