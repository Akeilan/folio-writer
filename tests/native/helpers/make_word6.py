"""Writes tests/data/import/sample6.doc: a small Word 6.0 document (W3-05's fixture),
made byte by byte here so the test doesn't depend on files from elsewhere.

Body: a heading, a paragraph with bold, italic red 14 pt text and a footnote, two
bulleted paragraphs (Word 6 numbering, ANLD), a 2x2 table and a second, landscape
section. Section 1 has a header. Usage: python3 make_word6.py OUT.doc"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "app"))
from folio.native.docwrite import cfb  # noqa: E402


def s1(op, v):
    return bytes([op, v & 0xFF])


def s2(op, v):
    return bytes([op]) + struct.pack("<h" if v < 0 else "<H", v)


class Story:
    def __init__(self):
        self.text = bytearray()
        self.runs = []     # (cp0, cp1, grpprl)
        self.paras = []    # (cp end, istd, grpprl)

    def add(self, t, g=b""):
        cp = len(self.text)
        self.text += t.encode("cp1252")
        self.runs.append((cp, len(self.text), g))

    def para(self, istd=0, g=b"", mark="\r"):
        self.add(mark)
        self.paras.append((len(self.text), istd, g))


def anld_bullet():
    a = bytearray(52)
    a[0] = 23                  # nfc: bullet
    a[1] = 1                   # one character before the number: the bullet itself
    struct.pack_into("<H", a, 6, 1)        # ftc: Symbol
    struct.pack_into("<H", a, 10, 1)       # start at
    struct.pack_into("<h", a, 12, 360)     # indent
    a[20] = 0xB7
    return bytes([12, len(a)]) + bytes(a)


def brc(width=1):
    return width | (1 << 3)    # single line


def deftable(ncols, width):
    centers = [-108 + width * k for k in range(ncols + 1)]
    data = bytes([ncols]) + b"".join(struct.pack("<h", c) for c in centers)
    data += b"".join(struct.pack("<HHHHH", 0, brc(), brc(), brc(), brc()) for _ in range(ncols))
    return bytes([190]) + struct.pack("<H", len(data) + 1) + data


def build():
    main = Story()
    main.add("Word 6 import test")
    main.para(1)
    main.add("Plain then ")
    main.add("bold", s1(85, 1))
    main.add(" and ")
    main.add("italic", s1(86, 1) + s1(98, 6) + s2(99, 28))
    fn_cp = len(main.text)
    main.add("\x02", s1(117, 1) + s1(104, 1))
    main.add(".")
    main.para(0, s1(5, 3))                               # justified
    for t in ("First bullet", "Second bullet"):
        main.add(t)
        main.para(0, anld_bullet() + s1(13, 11) + s2(17, 360) + s2(19, -360))
    tbl = deftable(2, 2880)
    for row in (("A1", "B1"), ("A2", "B2")):
        for c in row:
            main.add(c)
            main.para(0, s1(24, 1), mark="\x07")
        main.para(0, s1(24, 1) + s1(25, 1) + tbl, mark="\x07")
    main.add("After the table")
    main.para(0, mark="\x0c")
    sect1_end = len(main.text)
    main.add("Landscape section")
    main.para(0)
    ftn = Story()
    ftn.add("\x02", s1(117, 1) + s1(104, 1))
    ftn.add(" Note text")
    ftn.para(2)
    hdd = Story()
    hdd.add("Header text")
    hdd.para(3)
    tail = Story()
    tail.para(0)

    fc_min = 0x300
    stories = [(main, 0), (ftn, len(main.text)), (hdd, len(main.text) + len(ftn.text)),
               (tail, len(main.text) + len(ftn.text) + len(hdd.text))]
    text = b"".join(bytes(s.text) for s, _ in stories)
    wd = bytearray(fc_min) + text
    fc_mac = len(wd)
    # FKPs
    while len(wd) % 512:
        wd.append(0)
    runs = [(fc_min + b0 + a, fc_min + b0 + z, g) for s, b0 in stories for a, z, g in s.runs]
    page = bytearray(512)
    crun = len(runs)
    heap = 511
    offs = []
    for a, z, g in runs:
        if g:
            heap = (heap - 1 - len(g)) & ~1
            page[heap] = len(g)
            page[heap + 1:heap + 1 + len(g)] = g
            offs.append(heap // 2)
        else:
            offs.append(0)
    fcs = [runs[0][0]] + [z for _, z, _ in runs]
    for k, fc in enumerate(fcs):
        struct.pack_into("<I", page, 4 * k, fc)
    for k, o in enumerate(offs):
        page[4 * (crun + 1) + k] = o
    page[511] = crun
    assert 4 * (crun + 1) + crun < heap
    pn_chp = len(wd) // 512
    wd += page
    paras = []
    for s, b0 in stories:
        prev = 0
        for z, istd, g in s.paras:
            paras.append((fc_min + b0 + prev, fc_min + b0 + z, istd, g))
            prev = z
    page = bytearray(512)
    cpara = len(paras)
    heap = 511
    bxs = []
    for a, z, istd, g in paras:
        body = bytes([istd]) + g
        if len(body) % 2:
            body += b"\x00"
        enc = bytes([len(body) // 2]) + body
        heap = (heap - len(enc)) & ~1
        page[heap:heap + len(enc)] = enc
        bxs.append(heap // 2)
    fcs = [paras[0][0]] + [z for _, z, _, _ in paras]
    for k, fc in enumerate(fcs):
        struct.pack_into("<I", page, 4 * k, fc)
    for k, o in enumerate(bxs):
        page[4 * (cpara + 1) + 7 * k] = o
    page[511] = cpara
    assert 4 * (cpara + 1) + 7 * cpara < heap
    pn_pap = len(wd) // 512
    wd += page
    # the tables, all in WordDocument
    pairs = [(0, 0)] * 38

    def put(idx, data):
        while len(wd) % 2:
            wd.append(0)
        pairs[idx] = (len(wd), len(data))
        wd.extend(data)

    # SEPX
    sepx = []
    for g in (s1(153, 0x02) + s1(142, 2),
              s1(162, 2) + s2(164, 15840) + s2(165, 12240) + s1(153, 0) + s1(142, 2)):
        while len(wd) % 2:
            wd.append(0)
        sepx.append(len(wd))
        wd.extend(struct.pack("<H", len(g)) + g)
    # styles: Normal, heading 1, footnote text, header
    names = [(0, "Normal", s2(21, 0), b""), (1, "heading 1", s1(8, 1) + s2(21, 240) + s2(22, 60), s1(85, 1) + s2(99, 32)),
             (29, "footnote text", b"", s2(99, 20)), (31, "header", b"", b"")]
    stshi = struct.pack("<HHHHHHH", len(names), 8, 1, 0x4B, 0x0F, 0, 0)
    stsh = bytearray(struct.pack("<H", len(stshi)) + stshi)
    for istd, (sti, name, pap, chp) in enumerate(names):
        base = 0x0FFF if istd == 0 else 0
        body = bytearray(struct.pack("<HHHH", sti, 1 | (base << 4), 2 | (0 << 4), 0))
        body += bytes([len(name)]) + name.encode("cp1252") + b"\x00"
        for u in (struct.pack("<H", istd) + pap, chp):
            if len(body) % 2:
                body.append(0)
            body += struct.pack("<H", len(u)) + u
        stsh += struct.pack("<H", len(body)) + body
    put(1, bytes(stsh))
    pairs[0] = pairs[1]
    # notes, sections, headers
    put(2, struct.pack("<II", fn_cp, len(main.text)) + struct.pack("<H", 1))
    put(3, struct.pack("<III", 0, len(ftn.text), len(ftn.text) + 1))
    put(6, struct.pack("<III", 0, sect1_end, len(main.text)) +
        b"".join(struct.pack("<HIHI", 0, fc, 0, 0xFFFFFFFF) for fc in sepx))
    put(11, struct.pack("<II", 0, len(hdd.text)))
    put(12, struct.pack("<II", fcs[0] if False else runs[0][0], runs[-1][1]) + struct.pack("<H", pn_chp))
    put(13, struct.pack("<II", paras[0][0], paras[-1][1]) + struct.pack("<H", pn_pap))
    ffn = bytearray()
    for name, chs in (("Times New Roman", 0), ("Symbol", 2), ("Arial", 0)):
        body = bytes([0x16]) + struct.pack("<H", 400) + bytes([chs, 0]) + name.encode() + b"\x00"
        ffn += bytes([len(body)]) + body
    put(15, struct.pack("<H", len(ffn) + 2) + bytes(ffn))
    dop = bytearray(84)
    struct.pack_into("<H", dop, 10, 720)
    put(31, bytes(dop))
    # FIB
    fib = bytearray(0x1A2)
    struct.pack_into("<HHHHH", fib, 0, 0xA5DC, 0x65, 0x6A62, 0x0409, 0)
    struct.pack_into("<H", fib, 0x0C, 0x65)
    struct.pack_into("<II", fib, 0x18, fc_min, fc_mac)
    struct.pack_into("<I", fib, 0x20, len(wd))
    struct.pack_into("<iiii", fib, 0x34, len(main.text), len(ftn.text), len(hdd.text), 0)
    for k, (fc, lcb) in enumerate(pairs):
        struct.pack_into("<II", fib, 0x58 + 8 * k, fc, lcb)
    struct.pack_into("<HHHH", fib, 0x18A, pn_chp, pn_pap, 1, 1)
    wd[0:len(fib)] = fib
    return cfb({"WordDocument": bytes(wd)})


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "..", "data", "import", "sample6.doc")
    with open(out, "wb") as fh:
        fh.write(build())
    print(out)
