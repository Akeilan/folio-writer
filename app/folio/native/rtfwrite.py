"""Rich Text Format written by Folio itself (W3-01), from the document model (docxread
reads the .docx the engine saves): the font, colour and style tables, lists, sections with
headers and footers, paragraphs and runs with their formatting, tables, fields and
hyperlinks, footnotes and endnotes, pictures, bookmarks and comments — what Word writes for
the same document, in RTF 1.9 as Word reads it."""
from . import docxbuild as B

NFC = {"decimal": 0, "upperRoman": 1, "lowerRoman": 2, "upperLetter": 3, "lowerLetter": 4,
       "ordinal": 5, "cardinalText": 6, "ordinalText": 7, "decimalZero": 22, "bullet": 23,
       "none": 255}
UL = {"single": "ul", "double": "uldb", "thick": "ulth", "dotted": "uld", "dash": "uldash",
      "dotDash": "uldashd", "dotDotDash": "uldashdd", "wave": "ulwave", "words": "ulw",
      "dottedHeavy": "ulthd", "dashLong": "ulldash", "wavyDouble": "ululdbwave"}
BRD = {"single": "brdrs", "thick": "brdrth", "double": "brdrdb", "dotted": "brdrdot",
       "dashed": "brdrdash", "dashSmallGap": "brdrdashsm", "dotDash": "brdrdashd",
       "dotDotDash": "brdrdashdd", "triple": "brdrtriple", "wave": "brdrwavy",
       "doubleWave": "brdrwavydb", "inset": "brdrinset", "outset": "brdroutset",
       "thinThickSmallGap": "brdrthtnsg", "thickThinSmallGap": "brdrtnthsg",
       "threeDEmboss": "brdremboss", "threeDEngrave": "brdrengrave"}
HIGHLIGHT = {"black": 1, "blue": 2, "cyan": 3, "green": 4, "magenta": 5, "red": 6, "yellow": 7,
             "white": 8, "darkBlue": 9, "darkCyan": 10, "darkGreen": 11, "darkMagenta": 12,
             "darkRed": 13, "darkYellow": 14, "darkGray": 15, "lightGray": 16}
LANG = {"en-US": 1033, "en-GB": 2057, "en-AU": 3081, "en-CA": 4105, "de-DE": 1031, "fr-FR": 1036,
        "es-ES": 3082, "it-IT": 1040, "nl-NL": 1043, "nl-BE": 2067, "pt-BR": 1046, "pt-PT": 2070,
        "sv-SE": 1053, "nb-NO": 1044, "da-DK": 1030, "fi-FI": 1035, "pl-PL": 1045, "cs-CZ": 1029,
        "hu-HU": 1038, "ru-RU": 1049, "el-GR": 1032, "tr-TR": 1055, "ja-JP": 1041, "zh-CN": 2052,
        "zh-TW": 1028, "ko-KR": 1042, "he-IL": 1037, "ar-SA": 1025}
TLEAD = {"dot": "tldot", "hyphen": "tlhyph", "underscore": "tlul", "heavy": "tlth",
         "middleDot": "tlmdot"}


def esc(s):
    out = []
    for ch in s:
        o = ord(ch)
        if ch in "\\{}":
            out.append("\\" + ch)
        elif ch == "\t":
            out.append("\\tab ")
        elif ch in "\n\x0b":
            out.append("\\line ")
        elif ch == "\u00a0":
            out.append("\\~")
        elif ch == "\u00ad":
            out.append("\\-")
        elif ch == "\u2011":
            out.append("\\_")
        elif o < 32:
            continue
        elif o < 128:
            out.append(ch)
        elif o < 256:
            # Latin-1 is cp1252 except 0x80-0x9f; \'hh where they agree, \u otherwise
            try:
                b = ch.encode("cp1252")
                out.append("\\'%02x" % b[0])
            except UnicodeEncodeError:
                out.append("\\u%d?" % o)
        elif o < 0x10000:
            try:
                b = ch.encode("cp1252")
                out.append("\\u%d\\'%02x" % (o if o < 32768 else o - 65536, b[0]))
            except UnicodeEncodeError:
                out.append("\\u%d?" % (o if o < 32768 else o - 65536))
        else:
            # outside the basic plane: a surrogate pair
            v = o - 0x10000
            hi, lo = 0xD800 + (v >> 10), 0xDC00 + (v & 0x3FF)
            out.append("\\u%d?\\u%d?" % (hi - 65536, lo - 65536))
    return "".join(out)


class Writer:
    def __init__(self, doc):
        self.doc = doc
        self.fonts = []
        self.colors = []
        self.style_n = {}
        self.cstyle_n = {}
        self.tstyle_n = {}
        self.comment_ids = {}

    # ------------------------------------------------------------------ tables
    def font(self, name):
        name = name or "Calibri"
        if name not in self.fonts:
            self.fonts.append(name)
        return self.fonts.index(name)

    def color(self, hexv):
        if not hexv or hexv == "auto":
            return 0
        hexv = hexv.upper()
        if hexv not in self.colors:
            self.colors.append(hexv)
        return self.colors.index(hexv) + 1

    # -------------------------------------------------------------- properties
    def chp(self, r, base=None):
        out = []
        if r.get("font"):
            out.append("\\f%d" % self.font(r["font"]))
        if r.get("sz"):
            out.append("\\fs%d" % r["sz"])
        for k, cw in (("b", "b"), ("i", "i"), ("strike", "strike"), ("caps", "caps"),
                      ("smallcaps", "scaps"), ("hidden", "v"), ("outline", "outl"),
                      ("shadow", "shad"), ("emboss", "embo"), ("imprint", "impr")):
            if k in r:
                out.append("\\%s" % cw if r[k] else "\\%s0" % cw)
        if r.get("dstrike"):
            out.append("\\striked1")
        if "u" in r:
            if r["u"]:
                out.append("\\" + UL.get(r["u"] if isinstance(r["u"], str) else "single", "ul"))
            else:
                out.append("\\ulnone")
        if r.get("color"):
            out.append("\\cf%d" % self.color(r["color"]))
        if r.get("highlight") and r["highlight"] in HIGHLIGHT:
            out.append("\\highlight%d" % HIGHLIGHT[r["highlight"]])
        if r.get("shd"):
            out.append("\\chcbpat%d" % self.color(r["shd"]))
        if r.get("vert") == "superscript":
            out.append("\\super")
        elif r.get("vert") == "subscript":
            out.append("\\sub")
        if r.get("position"):
            p = r["position"]
            out.append("\\up%d" % p if p > 0 else "\\dn%d" % -p)
        if r.get("spacing"):
            out.append("\\expndtw%d" % r["spacing"])
        if r.get("scale") and r["scale"] != 100:
            out.append("\\charscalex%d" % r["scale"])
        if r.get("lang") in LANG:
            out.append("\\lang%d" % LANG[r["lang"]])
        return "".join(out)

    def pap(self, p, style=None, in_table=0):
        out = ["\\pard\\plain"]
        if style and style in self.style_n:
            out.append("\\s%d" % self.style_n[style])
        if in_table:
            out.append("\\intbl")
            if in_table > 1:
                out.append("\\itap%d" % in_table)
        al = p.get("align")
        out.append({"center": "\\qc", "right": "\\qr", "end": "\\qr", "both": "\\qj",
                    "distribute": "\\qd"}.get(al, "\\ql"))
        if "ind_l" in p:
            out.append("\\li%d\\lin%d" % (p["ind_l"], p["ind_l"]))
        if "ind_r" in p:
            out.append("\\ri%d\\rin%d" % (p["ind_r"], p["ind_r"]))
        if "ind_first" in p:
            out.append("\\fi%d" % p["ind_first"])
        if "sb" in p:
            out.append("\\sb%d" % p["sb"])
        if "sa" in p:
            out.append("\\sa%d" % p["sa"])
        if "line" in p:
            rule = p.get("line_rule", "auto")
            if rule == "auto":
                out.append("\\sl%d\\slmult1" % p["line"])
            elif rule == "exact":
                out.append("\\sl-%d\\slmult0" % p["line"])
            else:
                out.append("\\sl%d\\slmult0" % p["line"])
        if p.get("keep_next"):
            out.append("\\keepn")
        if p.get("keep_lines"):
            out.append("\\keep")
        if p.get("pbb"):
            out.append("\\pagebb")
        if "widow" in p:
            out.append("\\widctlpar" if p["widow"] else "\\nowidctlpar")
        if p.get("contextual"):
            out.append("\\contextualspace")
        if p.get("bidi"):
            out.append("\\rtlpar")
        if p.get("outline") is not None:
            out.append("\\outlinelevel%d" % p["outline"])
        if p.get("num") is not None:
            n, lvl = p["num"]
            if n >= 0:
                out.append("\\ls%d\\ilvl%d" % (n + 1, lvl))
        for pos, kind, leader in p.get("tabs") or []:
            if leader and leader in TLEAD:
                out.append("\\" + TLEAD[leader])
            if kind == "bar":
                out.append("\\tb%d" % pos)
                continue
            out.append({"right": "\\tqr", "center": "\\tqc", "decimal": "\\tqdec"}.get(kind, ""))
            out.append("\\tx%d" % pos)
        for side, cw in (("top", "brdrt"), ("left", "brdrl"), ("bottom", "brdrb"), ("right", "brdrr"),
                         ("between", "brdrbtw")):
            b = (p.get("borders") or {}).get(side)
            if b:
                out.append("\\" + cw + self.border(b))
        if p.get("shd"):
            out.append("\\cbpat%d" % self.color(p["shd"]))
        return "".join(out) + " "

    def border(self, b):
        sz, color, kind, space = (list(b) + [None] * 4)[:4]
        s = "\\" + BRD.get(kind or "single", "brdrs") + "\\brdrw%d" % max(1, int(round((sz or 4) * 20 / 8.0)))
        if space:
            s += "\\brsp%d" % (space * 20)
        if color and color != "auto":
            s += "\\brdrcf%d" % self.color(color)
        return s

    # ------------------------------------------------------------------ content
    def runs(self, runs):
        out = []
        for r in runs:
            t = r.get("t")
            fmt = self.chp(r.get("rpr", {}))
            cs = r.get("cstyle")
            if cs and cs in self.cstyle_n:
                fmt = "\\cs%d" % self.cstyle_n[cs] + fmt
            if t == "text":
                if r.get("text"):
                    out.append("{%s %s}" % (fmt, esc(r["text"])) if fmt else esc(r["text"]))
            elif t == "tab":
                out.append("{%s\\tab}" % fmt)
            elif t == "br":
                out.append("{%s\\line}" % fmt)
            elif t == "page":
                out.append("{%s\\page}" % fmt)
            elif t == "col":
                out.append("{%s\\column}" % fmt)
            elif t == "image":
                out.append(self.picture(r))
            elif t == "note":
                end = r.get("kind") == "endnote"
                body = self.blocks(r.get("blocks") or [B.para()], note=True)
                out.append("{%s\\super\\chftn}{\\footnote%s\\pard\\plain{\\super\\chftn}%s}" % (
                    fmt, "\\ftnalt" if end else "", body))
            elif t == "field":
                res = r.get("result", "")
                res_rtf = self.runs(res) if isinstance(res, list) else "{%s %s}" % (fmt, esc(str(res or "")))
                out.append("{\\field{\\*\\fldinst {%s %s}}{\\fldrslt %s}}" % (fmt, esc(r.get("instr", "")), res_rtf))
            elif t == "fbegin":
                out.append("{\\field{\\*\\fldinst {%s %s}}{\\fldrslt " % (fmt, esc(r.get("instr", ""))))
            elif t == "fsep":
                pass
            elif t == "fend":
                out.append("}}")
            elif t == "link":
                inner = self.runs(r.get("runs", []))
                if r.get("url"):
                    url = r["url"]
                    anchor = ""
                    if "#" in url:
                        url, anchor = url.split("#", 1)
                    instr = 'HYPERLINK "%s"' % url + (' \\l "%s"' % anchor if anchor else "")
                    out.append('{\\field{\\*\\fldinst {%s}}{\\fldrslt %s}}' % (esc(instr), inner))
                elif r.get("anchor"):
                    out.append('{\\field{\\*\\fldinst {HYPERLINK \\\\l "%s"}}{\\fldrslt %s}}' % (esc(r["anchor"]), inner))
                else:
                    out.append(inner)
            elif t == "bmstart":
                out.append("{\\*\\bkmkstart %s}" % esc(r["name"]))
            elif t == "bmend":
                out.append("{\\*\\bkmkend %s}" % esc(r["name"]))
            elif t == "cstart":
                out.append("{\\*\\atrfstart %d}" % r["id"])
            elif t == "cend":
                out.append(self.comment(r["id"]))
        return "".join(out)

    def comment(self, cid):
        c = next((c for c in self.doc.comments if c.get("id") == cid), None)
        if c is None:
            return "{\\*\\atrfend %d}" % cid
        author = c.get("author") or "Author"
        initials = c.get("initials") or "".join(w[:1] for w in author.split())[:4]
        body = self.blocks(c.get("blocks") or [B.para()], note=True)
        return ("{\\*\\atrfend %d}{\\*\\atnid %s}{\\*\\atnauthor %s}\\chatn{\\*\\annotation"
                "{\\*\\atnref %d}%s}" % (cid, esc(initials), esc(author), cid, body))

    def picture(self, r):
        ext = (r.get("ext") or "png").lower()
        kind = {"png": "\\pngblip", "jpg": "\\jpegblip", "jpeg": "\\jpegblip", "emf": "\\emfblip",
                "wmf": "\\wmetafile8"}.get(ext)
        data = r.get("data") or b""
        if kind is None or not data:
            return ""
        wg = int(r.get("cx", 0) / B.EMU_PER_TWIP) or 1440
        hg = int(r.get("cy", 0) / B.EMU_PER_TWIP) or 1440
        w, h = _pixel_size(data, ext) or (wg // 15, hg // 15)
        hx = data.hex()
        lines = "\n".join(hx[i:i + 128] for i in range(0, len(hx), 128))
        return ("{\\*\\shppict{\\pict%s\\picw%d\\pich%d\\picwgoal%d\\pichgoal%d\n%s}}" % (
            kind, w, h, wg, hg, lines))

    def para(self, b, in_table=0, last_in_cell=False, nest=0):
        style = b.get("style")
        head = self.pap(b.get("ppr", {}), style, in_table)
        body = self.runs(b.get("runs", []))
        mark = self.chp(b.get("rpr") or {})
        if last_in_cell:
            end = "\\nestcell" if in_table > 1 else "\\cell"
        else:
            end = "\\par"
        return head + body + ("{%s%s}" % (mark, end) if mark else end) + "\n"

    def table(self, t, depth=1):
        out = []
        cols = t.get("cols") or []
        ncol = max((sum(c.get("span", 1) for c in r["cells"]) for r in t["rows"]), default=1)
        if not cols:
            cols = [9360 // max(1, ncol)] * ncol
        left = t.get("indent", 0)
        for row in t["rows"]:
            if not row.get("cells"):
                continue
            rowdef = self.rowdef(t, row, cols, left)
            cells = row["cells"]
            body = []
            for c in cells:
                blocks = c.get("blocks") or [B.para()]
                for i, b in enumerate(blocks):
                    last = i == len(blocks) - 1
                    if b.get("table"):
                        body.append(self.table(b, depth + 1))
                        if last:
                            body.append(self.pap({}, None, depth) + ("\\nestcell" if depth > 1 else "\\cell") + "\n")
                    else:
                        body.append(self.para(b, depth, last))
            if depth == 1:
                out.append(rowdef + "\n" + "".join(body) + "\\pard\\intbl" + rowdef + "\\row\n")
            else:
                out.append("".join(body) + "{\\*\\nesttableprops" + rowdef + "\\nestrow}"
                           "{\\nonesttables\\par}\n")
        return "".join(out)

    def rowdef(self, t, row, cols, left):
        s = ["\\trowd\\trgaph108\\trleft%d" % (left - 108 if left else -108)]
        if t.get("align") == "center":
            s.append("\\trqc")
        elif t.get("align") == "right":
            s.append("\\trqr")
        if row.get("header"):
            s.append("\\trhdr")
        if row.get("cant_split"):
            s.append("\\trkeep")
        if row.get("height"):
            s.append("\\trrh%d" % (-row["height"] if row.get("exact") else row["height"]))
        default_borders = t.get("borders", True) and not t.get("style")
        x = left
        ci = 0
        for c in row["cells"]:
            span = c.get("span", 1)
            w = sum(cols[ci:ci + span]) if ci + span <= len(cols) else (c.get("width") or 2160)
            ci += span
            x += w
            if c.get("vmerge") == "restart":
                s.append("\\clvmgf")
            elif c.get("vmerge") == "cont":
                s.append("\\clvmrg")
            if c.get("valign"):
                s.append({"top": "\\clvertalt", "center": "\\clvertalc", "bottom": "\\clvertalb"}.get(c["valign"], ""))
            bd = c.get("borders")
            for side, cw in (("top", "clbrdrt"), ("left", "clbrdrl"), ("bottom", "clbrdrb"), ("right", "clbrdrr")):
                b = (bd or {}).get(side)
                if b:
                    s.append("\\" + cw + self.border(b))
                elif default_borders and bd is None:
                    s.append("\\" + cw + "\\brdrs\\brdrw10")
            if c.get("shd"):
                s.append("\\clcbpat%d" % self.color(c["shd"]))
            s.append("\\clwWidth%d\\clftsWidth3\\cellx%d" % (w, x))
        return "".join(s)

    def blocks(self, blocks, note=False):
        out = []
        for b in blocks:
            if b.get("table"):
                if any(r.get("cells") for r in b.get("rows", [])):
                    out.append(self.table(b))
            else:
                out.append(self.para(b))
        s = "".join(out)
        if note and s.endswith("\\par\n"):
            # the last paragraph of a note or header ends with its group
            s = s[:-len("\\par\n")] + "\n"
        return s

    def section(self, sec, first):
        s = ["" if first else "\\sect", "\\sectd"]
        brk = sec.get("break")
        s.append({"continuous": "\\sbknone", "nextColumn": "\\sbkcol", "evenPage": "\\sbkeven",
                  "oddPage": "\\sbkodd"}.get(brk, "\\sbkpage"))
        s.append("\\pgwsxn%d\\pghsxn%d" % (sec["w"], sec["h"]))
        m = sec["margins"]
        s.append("\\marglsxn%d\\margrsxn%d\\margtsxn%d\\margbsxn%d\\guttersxn%d\\headery%d\\footery%d" % (
            m["left"], m["right"], m["top"], m["bottom"], m.get("gutter", 0), m.get("header", 720), m.get("footer", 720)))
        if sec.get("landscape"):
            s.append("\\lndscpsxn")
        if sec.get("cols", 1) > 1:
            s.append("\\cols%d\\colsx%d" % (sec["cols"], sec.get("col_space", 720)))
        if sec.get("title_pg"):
            s.append("\\titlepg")
        if sec.get("page_start"):
            s.append("\\pgnrestart\\pgnstarts%d" % sec["page_start"])
        for kind, store, words in (("header", sec.get("headers", {}), {"default": "header", "even": "headerl", "first": "headerf"}),
                                   ("footer", sec.get("footers", {}), {"default": "footer", "even": "footerl", "first": "footerf"})):
            for typ, cw in words.items():
                if typ in store:
                    s.append("{\\%s %s}" % (cw, self.blocks(store[typ], note=True)))
        return "".join(s) + "\n"

    # -------------------------------------------------------------- styles, lists
    def stylesheet(self):
        d = self.doc
        # numbers: Normal 0, then the rest
        n = 1
        for st in d.styles:
            if st["type"] == "paragraph":
                if st.get("default") or st["id"] == "Normal":
                    self.style_n.setdefault(st["id"], 0)
                else:
                    self.style_n[st["id"]] = n
                    n += 1
        for st in d.styles:
            if st["type"] == "character":
                self.cstyle_n[st["id"]] = n
                n += 1
            elif st["type"] == "table":
                self.tstyle_n[st["id"]] = n
                n += 1
        out = []
        for st in d.styles:
            kind = st["type"]
            if kind == "paragraph":
                num = self.style_n[st["id"]]
                head = "{\\s%d" % num + self.pap(st.get("ppr", {})).replace("\\pard\\plain", "").rstrip()
            elif kind == "character":
                num = self.cstyle_n[st["id"]]
                head = "{\\*\\cs%d \\additive" % num
            elif kind == "table":
                num = self.tstyle_n[st["id"]]
                head = "{\\*\\ts%d\\tsrowd" % num
            else:
                continue
            based = st.get("based")
            table = self.style_n if kind == "paragraph" else self.cstyle_n if kind == "character" else self.tstyle_n
            if based and based in table and based != st["id"]:
                head += "\\sbasedon%d" % table[based]
            nxt = st.get("next")
            if kind == "paragraph":
                head += "\\snext%d" % self.style_n.get(nxt, num)
            if st.get("default") or (kind == "paragraph" and st.get("name") in ("Normal",)):
                head += "\\sqformat"
            head += self.chp(st.get("rpr", {}))
            out.append("%s %s;}" % (head, esc(st.get("name") or st["id"])))
        return "{\\stylesheet\n%s}\n" % "\n".join(out)

    def listtables(self):
        d = self.doc
        if not d.lists:
            return ""
        lt = []
        for li, levels in enumerate(d.lists):
            lv_out = []
            for i, lv in enumerate(levels[:9]):
                fmt = lv.get("fmt", "decimal")
                text = lv.get("text")
                if text is None:
                    text = lv.get("bullet", "\u2022") if fmt == "bullet" else "%%%d." % (i + 1)
                # \leveltext: length, the text with each %N as a level number placeholder
                body = []
                nums = []
                k = 0
                while k < len(text):
                    if text[k] == "%" and k + 1 < len(text) and text[k + 1].isdigit():
                        body.append("\\'%02x" % (int(text[k + 1]) - 1))
                        nums.append(len(body))
                        k += 2
                        continue
                    body.append(esc(text[k]))
                    k += 1
                ltext = "{\\leveltext\\'%02x%s;}" % (len(body), "".join(body))
                lnums = "{\\levelnumbers%s;}" % "".join("\\'%02x" % n for n in nums)
                font = ""
                if lv.get("font"):
                    font = "\\f%d" % self.font(lv["font"])
                ind = lv.get("ind", 720 * (i + 1))
                hang = lv.get("hang", 360)
                lv_out.append("{\\listlevel\\levelnfc%d\\levelnfcn%d\\leveljc%d\\leveljcn%d\\levelfollow0"
                              "\\levelstartat%d%s%s%s\\fi-%d\\li%d\\lin%d}" % (
                                  NFC.get(fmt, 0), NFC.get(fmt, 0),
                                  {"left": 0, "center": 1, "right": 2}.get(lv.get("jc", "left"), 0),
                                  {"left": 0, "center": 1, "right": 2}.get(lv.get("jc", "left"), 0),
                                  lv.get("start", 1), ltext, lnums, font, hang, ind, ind))
            lt.append("{\\list\\listtemplateid%d%s{\\listname ;}\\listid%d}" % (
                1000 + li, "".join(lv_out), li + 1))
        lo = []
        for ni, (ai, restart) in enumerate(d.nums):
            extra = ""
            if restart:
                extra = "\\listoverridecount9" + "".join(
                    "{\\lfolevel\\listoverridestartat\\levelstartat%d}" % lv.get("start", 1)
                    for lv in d.lists[ai][:9])
            else:
                extra = "\\listoverridecount0"
            lo.append("{\\listoverride\\listid%d%s\\ls%d}" % (ai + 1, extra, ni + 1))
        return "{\\*\\listtable\n%s}\n{\\*\\listoverridetable\n%s}\n" % ("\n".join(lt), "\n".join(lo))

    def info(self):
        m = self.doc.meta or {}
        parts = []
        for key, cw in (("title", "title"), ("subject", "subject"), ("creator", "author"),
                        ("keywords", "keywords"), ("description", "doccomm")):
            if m.get(key):
                parts.append("{\\%s %s}" % (cw, esc(m[key])))
        return "{\\info%s}" % "".join(parts) if parts else ""

    def document(self):
        d = self.doc
        dr = d.defaults.get("rpr", {})
        dfont = self.font(dr.get("font") or "Calibri")
        styles = self.stylesheet()
        lists = self.listtables()
        body = []
        secs = d.sections or [B.section()]
        s0 = secs[0]
        for i, sec in enumerate(secs):
            body.append(self.section(sec, i == 0))
            body.append(self.blocks(sec["blocks"] or [B.para()]))
        content = "".join(body)
        # page setup for the whole document as Word writes it (the first section's)
        m = s0["margins"]
        docfmt = "\\paperw%d\\paperh%d\\margl%d\\margr%d\\margt%d\\margb%d\\gutter%d%s" % (
            s0["w"], s0["h"], m["left"], m["right"], m["top"], m["bottom"], m.get("gutter", 0),
            "\\landscape" if s0.get("landscape") else "")
        fonts = "".join("{\\f%d\\fnil\\fcharset0 %s;}" % (i, esc(f)) for i, f in enumerate(self.fonts))
        colors = ";" + "".join("\\red%d\\green%d\\blue%d;" % (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16))
                               for c in self.colors)
        dsz = dr.get("sz") or 22
        return ("{\\rtf1\\ansi\\ansicpg1252\\deff%d\\uc1\\deflang1033\n{\\fonttbl%s}\n{\\colortbl%s}\n"
                "{\\*\\defchp \\f%d\\fs%d}{\\*\\defpap \\ql\\sa160\\sl259\\slmult1}\n%s%s"
                "{\\*\\generator Folio Writer;}%s\n\\deftab%d\\viewkind1%s\\fet0\n%s}\n" % (
                    dfont, fonts, colors, dfont, dsz, styles, lists, self.info(), d.tab_stop or 720,
                    docfmt, content))


def _pixel_size(data, ext):
    import struct
    try:
        if ext == "png" and data[:8] == b"\x89PNG\r\n\x1a\n":
            return struct.unpack(">II", data[16:24])
        if ext in ("jpg", "jpeg") and data[:2] == b"\xff\xd8":
            i = 2
            while i < len(data) - 9:
                if data[i] != 0xFF:
                    i += 1
                    continue
                mk = data[i + 1]
                ln = struct.unpack(">H", data[i + 2:i + 4])[0]
                if mk in (0xC0, 0xC1, 0xC2):
                    h, w = struct.unpack(">HH", data[i + 5:i + 9])
                    return w, h
                i += 2 + ln
    except struct.error:
        pass
    return None


def to_rtf(doc):
    """The document model as an RTF file's text (ASCII)."""
    return Writer(doc).document()


def docx_to_rtf_file(docx_path, rtf_path):
    from . import docxread
    text = to_rtf(docxread.read(docx_path))
    with open(rtf_path, "w", encoding="ascii", newline="\r\n") as fh:
        fh.write(text)
    return rtf_path
