"""Rich Text Format read by Folio itself (W3-01), into the document model of docxbuild:
fonts, colours, styles, lists, sections with headers and footers, paragraphs and runs with
their formatting, tables (merged cells, borders, shading, nested), fields and hyperlinks,
footnotes and endnotes, pictures, bookmarks and comments.

Word writes RTF 1.9; older and other writers (WordPad, LibreOffice, macOS TextEdit) are read
the same way. Destinations that carry nothing for the model are skipped."""
import re

from . import docxbuild as B

CHARSETS = {0: "cp1252", 1: "cp1252", 2: "cp1252", 77: "mac_roman", 128: "cp932", 129: "cp949",
            130: "johab", 134: "gbk", 136: "big5", 161: "cp1253", 162: "cp1254", 163: "cp1258",
            177: "cp1255", 178: "cp1256", 186: "cp1257", 204: "cp1251", 222: "cp874",
            238: "cp1250", 254: "cp437", 255: "cp850"}
# LCIDs Word writes most, as w:lang tags
LCID = {1033: "en-US", 2057: "en-GB", 3081: "en-AU", 4105: "en-CA", 1031: "de-DE", 1036: "fr-FR",
        1034: "es-ES", 3082: "es-ES", 1040: "it-IT", 1043: "nl-NL", 2067: "nl-BE", 1046: "pt-BR",
        2070: "pt-PT", 1053: "sv-SE", 1044: "nb-NO", 1030: "da-DK", 1035: "fi-FI", 1045: "pl-PL",
        1029: "cs-CZ", 1038: "hu-HU", 1049: "ru-RU", 1032: "el-GR", 1055: "tr-TR", 1041: "ja-JP",
        2052: "zh-CN", 1028: "zh-TW", 1042: "ko-KR", 1037: "he-IL", 1025: "ar-SA", 1024: None}
HIGHLIGHT = {1: "black", 2: "blue", 3: "cyan", 4: "green", 5: "magenta", 6: "red", 7: "yellow",
             9: "darkBlue", 10: "darkCyan", 11: "darkGreen", 12: "darkMagenta", 13: "darkRed",
             14: "darkYellow", 15: "darkGray", 16: "lightGray", 8: "white"}
HL_RGB = {"000000": 1, "0000FF": 2, "00FFFF": 3, "00FF00": 4, "FF00FF": 5, "FF0000": 6, "FFFF00": 7,
          "FFFFFF": 8, "000080": 9, "008080": 10, "008000": 11, "800080": 12, "800000": 13,
          "808000": 14, "808080": 15, "C0C0C0": 16}
NFC = {0: "decimal", 1: "upperRoman", 2: "lowerRoman", 3: "upperLetter", 4: "lowerLetter",
       5: "ordinal", 6: "cardinalText", 7: "ordinalText", 22: "decimalZero", 23: "bullet",
       255: "none", 47: "none"}
UNDERLINES = {"ul": "single", "uld": "dotted", "uldash": "dash", "uldashd": "dotDash",
              "uldashdd": "dotDotDash", "uldb": "double", "ulth": "thick", "ulw": "words",
              "ulwave": "wave", "ululdbwave": "wavyDouble", "ulldash": "dashLong",
              "ulthd": "dottedHeavy", "ulhwave": "wave", "ulthdash": "dashedHeavy"}
BORDERS = {"brdrs": "single", "brdrth": "thick", "brdrdb": "double", "brdrdot": "dotted",
           "brdrdash": "dashed", "brdrdashsm": "dashSmallGap", "brdrdashd": "dotDash",
           "brdrdashdd": "dotDotDash", "brdrtriple": "triple", "brdrwavy": "wave",
           "brdrwavydb": "doubleWave", "brdrinset": "inset", "brdroutset": "outset",
           "brdrsh": "single", "brdrnone": "nil", "brdrnil": "nil", "brdrthtnsg": "thinThickSmallGap",
           "brdrtnthsg": "thickThinSmallGap", "brdremboss": "threeDEmboss", "brdrengrave": "threeDEngrave"}
TAB_LEADERS = {"tldot": "dot", "tlhyph": "hyphen", "tlul": "underscore", "tlth": "heavy",
               "tleq": "middleDot", "tlmdot": "middleDot"}
SYMBOLS = {"emdash": "\u2014", "endash": "\u2013", "bullet": "\u2022", "lquote": "\u2018",
           "rquote": "\u2019", "ldblquote": "\u201c", "rdblquote": "\u201d", "emspace": "\u2003",
           "enspace": "\u2002", "qmspace": "\u2005", "zwj": "\u200d", "zwnj": "\u200c",
           "ltrmark": "\u200e", "rtlmark": "\u200f"}
# destinations whose text isn't document text
SKIP = {"fonttbl", "colortbl", "stylesheet", "info", "listtable", "listoverridetable",
        "revtbl", "rsidtbl", "generator", "xmlnstbl", "themedata", "colorschememapping",
        "latentstyles", "datastore", "pgdsctbl", "filetbl", "mmathPr", "operator",
        "userprops", "pnseclvl", "pntext", "pntxta", "pntxtb", "listtext", "fldtype",
        "wgrffmtfilter", "nonshppict", "bkmkend", "bkmkstart", "atnid", "atnauthor",
        "atndate", "atnref", "atrfstart", "atrfend", "atnparent", "atnicn", "atntime",
        "docvar", "template", "picprop", "blipuid", "shpinst", "xe", "tc", "objdata",
        "objclass", "result", "passwordhash", "protusertbl", "ftnsep", "ftnsepc", "aftnsep",
        "aftnsepc", "ftncn", "aftncn", "falt", "panose", "fname", "keycode", "leveltext",
        "levelnumbers", "listname", "liststylename", "author", "operator", "company",
        "hlinkbase", "title", "subject", "keywords", "doccomm", "category", "manager",
        "comment", "creatim", "revtim", "printim", "buptim", "mhtmltag", "htmltag",
        "background", "factoidname", "oldcprops", "oldpprops", "oldsprops", "oldtprops",
        "ud", "upr", "bookmarkstart", "macpict", "pnseclvl1", "sp", "sn", "sv", "nonesttables"}


class Tok:
    __slots__ = ("kind", "word", "arg", "text")

    def __init__(self, kind, word=None, arg=None, text=None):
        self.kind, self.word, self.arg, self.text = kind, word, arg, text


_TOKEN = re.compile(rb"\\([a-zA-Z]{1,32})(-?\d{1,10})? ?|\\'([0-9a-fA-F]{2})|\\(.)|([{}])|([\r\n]+)|([^\\{}\r\n]+)", re.S)


def tokens(data):
    pos = 0
    n = len(data)
    while pos < n:
        m = _TOKEN.match(data, pos)
        if not m:
            pos += 1
            continue
        pos = m.end()
        if m.group(1) is not None:
            word = m.group(1).decode("ascii")
            arg = int(m.group(2)) if m.group(2) is not None else None
            if word == "bin" and arg:
                yield Tok("bin", text=data[pos:pos + arg])
                pos += arg
                continue
            yield Tok("cw", word, arg)
        elif m.group(3) is not None:
            yield Tok("hex", arg=int(m.group(3), 16))
        elif m.group(4) is not None:
            yield Tok("sym", m.group(4).decode("latin-1"))
        elif m.group(5) is not None:
            yield Tok(m.group(5).decode())
        elif m.group(6) is not None:
            continue
        else:
            yield Tok("text", text=m.group(7))


def _new_chp():
    return {}


def _new_pap():
    return {"ppr": {}, "style": None, "intbl": False, "itap": 0, "ls": None, "ilvl": 0}


class State:
    """What a group carries: its destination and character / paragraph formatting."""

    def __init__(self):
        self.dest = "body"
        self.chp = _new_chp()
        self.pap = _new_pap()
        self.uc = 1
        self.skip = False
        self.font = None
        self.cstyle = None
        self.ignore_unknown = False

    def copy(self):
        s = State()
        s.dest = self.dest
        s.chp = dict(self.chp)
        s.pap = {"ppr": dict(self.pap["ppr"]), "style": self.pap["style"], "intbl": self.pap["intbl"],
                 "itap": self.pap["itap"], "ls": self.pap["ls"], "ilvl": self.pap["ilvl"]}
        if "tabs" in self.pap["ppr"]:
            s.pap["ppr"]["tabs"] = list(self.pap["ppr"]["tabs"])
        if "borders" in self.pap["ppr"]:
            s.pap["ppr"]["borders"] = dict(self.pap["ppr"]["borders"])
        s.uc = self.uc
        s.skip = self.skip
        s.font = self.font
        s.cstyle = self.cstyle
        s._nest = getattr(self, "_nest", False)
        return s


class Story:
    """Where text is going: a list of blocks being built (body, cell, header, note...)."""

    def __init__(self, blocks):
        self.blocks = blocks
        self.runs = []
        # tables being built, by nesting depth: {"rows": [...], "cur_cells": [...], "rowdef": {...}}
        self.tables = {}


class Reader:
    def __init__(self, data):
        self.data = data
        self.doc = B.Doc()
        self.fonts = {}          # n -> (name, codepage)
        self.colors = []
        self.styles = {}         # n -> style id (paragraph), "c"+n char, "t"+n table
        self.default_font = 0
        self.codepage = "cp1252"
        self.lists = {}          # listid -> abstract index
        self.ls = {}             # ls n -> num index
        self.sec = B.section()
        self.doc_sec = {}        # document-wide page setup (\paperw...)
        self.sec_props = {}
        self.story = Story(self.sec["blocks"])
        self.stories = []
        self.field_stack = []
        self.bm = {}
        self.comment_open = []
        self.comments = {}
        self.pending_hf = None
        self.deftab = 720
        self.tok = None

    # ---------------------------------------------------------------- tables of the header
    def charset(self, f):
        f = self.fonts.get(f)
        return f[1] if f else self.codepage

    # ------------------------------------------------------------------ run text
    def add_text(self, st, text):
        if not text or st.chp.get("_del"):
            # tracked deletions: the document as it reads with the changes accepted
            return
        r = self.story.runs
        rpr = self.run_props(st)
        if r and r[-1]["t"] == "text" and r[-1]["rpr"] == rpr and r[-1].get("cstyle") == st.cstyle:
            r[-1]["text"] += text
        else:
            run = {"t": "text", "text": text, "rpr": rpr}
            if st.cstyle:
                run["cstyle"] = st.cstyle
            r.append(run)

    def add_run(self, st, kind, **kw):
        run = {"t": kind, "rpr": self.run_props(st)}
        run.update(kw)
        self.story.runs.append(run)
        return run

    def run_props(self, st):
        r = dict(st.chp)
        r.pop("_del", None)
        f = r.pop("_f", None)
        if f is not None and f in self.fonts:
            r["font"] = self.fonts[f][0]
        return r

    # -------------------------------------------------------------- paragraphs
    def end_para(self, st, kind="par"):
        p = st.pap
        ppr = dict(p["ppr"])
        if p["ls"] is not None and p["ls"] in self.ls:
            ppr["num"] = (self.ls[p["ls"]], p["ilvl"])
        para = {"style": p["style"] or self.styles.get(0), "ppr": ppr, "rpr": self.run_props(st),
                "runs": self.story.runs}
        self.story.runs = []
        depth = p["itap"] if p["intbl"] else 0
        if depth and kind == "par":
            depth = max(1, depth)
        if depth:
            self.close_tables(depth)
            t = self.table(depth)
            t["cell"].append(para)
        else:
            self.close_tables(0)
            self.story.blocks.append(para)

    def table(self, depth):
        tabs = self.story.tables
        for d in range(1, depth + 1):
            if d not in tabs:
                tabs[d] = {"rows": [], "cells": [], "cell": [], "rowdef": None}
        return tabs[depth]

    def close_tables(self, keep):
        """Tables deeper than `keep` are finished (text came after them)."""
        tabs = self.story.tables
        for d in sorted([d for d in tabs if d > keep], reverse=True):
            t = tabs.pop(d)
            if t["cells"] or t["cell"]:
                # a row never ended: end it now
                self._finish_row(t, {"cells": []})
            if not t["rows"]:
                continue
            block = self._table_block(t)
            if d - 1 >= 1 and (d - 1) in tabs:
                tabs[d - 1]["cell"].append(block)
            else:
                self.story.blocks.append(block)

    def end_cell(self, st, depth):
        if self.story.runs or True:
            # the cell's last paragraph ends with the cell mark
            p = st.pap
            ppr = dict(p["ppr"])
            if p["ls"] is not None and p["ls"] in self.ls:
                ppr["num"] = (self.ls[p["ls"]], p["ilvl"])
            para = {"style": p["style"] or self.styles.get(0), "ppr": ppr, "rpr": self.run_props(st),
                    "runs": self.story.runs}
            self.story.runs = []
        t = self.table(depth)
        # a deeper table finished inside this cell
        self.close_tables(depth)
        t["cell"].append(para)
        t["cells"].append(t["cell"])
        t["cell"] = []

    def end_row(self, depth, rowdef):
        self.close_tables(depth)
        t = self.table(depth)
        self._finish_row(t, rowdef or t.get("rowdef") or {"cells": []})

    def _finish_row(self, t, rowdef):
        if t["cell"]:
            t["cells"].append(t["cell"])
            t["cell"] = []
        defs = rowdef.get("cells") or []
        cells = []
        prev_x = rowdef.get("left", 0)
        for i, blocks in enumerate(t["cells"]):
            d = defs[i] if i < len(defs) else {}
            x = d.get("x")
            w = (x - prev_x) if x is not None else 0
            if x is not None:
                prev_x = x
            c = {"blocks": blocks or [B.para()], "width": max(0, w)}
            for k in ("vmerge", "shd", "valign", "borders", "hmerge"):
                if d.get(k):
                    c[k] = d[k]
            cells.append(c)
        # horizontal merges (\clmgf + \clmrg): one cell spanning
        merged = []
        for c in cells:
            if c.get("hmerge") == "cont" and merged:
                merged[-1]["span"] = merged[-1].get("span", 1) + 1
                merged[-1]["width"] += c["width"]
                continue
            c.pop("hmerge", None)
            merged.append(c)
        row = {"cells": merged}
        if rowdef.get("header"):
            row["header"] = True
        if rowdef.get("height"):
            row["height"] = abs(rowdef["height"])
            if rowdef["height"] < 0:
                row["exact"] = True
        if rowdef.get("cant_split"):
            row["cant_split"] = True
        row["_def"] = rowdef
        t["rows"].append(row)
        t["cells"] = []

    def _table_block(self, t):
        rows = t["rows"]
        # columns: every cell edge in every row
        edges = set()
        for row in rows:
            x = row["_def"].get("left", 0)
            edges.add(x)
            for c in row["cells"]:
                x += c["width"]
                edges.add(x)
        edges = sorted(edges)
        cols = [b - a for a, b in zip(edges, edges[1:]) if b - a > 0]
        out = {"table": True, "rows": [], "cols": cols if cols else []}
        d0 = rows[0]["_def"]
        if d0.get("align"):
            out["align"] = d0["align"]
        if d0.get("left"):
            out["indent"] = d0["left"] + d0.get("gap", 0)
        any_borders = any(c.get("borders") for r in rows for c in r["cells"])
        out["borders"] = False if any_borders else d0.get("tborders", False)
        for row in rows:
            # spans against the column grid
            x = row["_def"].get("left", 0)
            for c in row["cells"]:
                a = edges.index(x) if x in edges else 0
                x += c["width"]
                b = edges.index(x) if x in edges else a + 1
                if b - a > 1:
                    c["span"] = b - a
                elif "span" in c:
                    c.pop("span")
            row.pop("_def", None)
            out["rows"].append(row)
        return out

    # -------------------------------------------------------------- control words
    def run(self):
        data = self.data
        stack = []
        st = State()
        dest_text = []
        self._group_text = []
        toks = tokens(data)
        pending_ast = False
        hexbuf = []

        def flush_hex(s):
            if hexbuf:
                b = bytes(hexbuf)
                hexbuf.clear()
                cp = self.charset(s.chp.get("_f", self.default_font) if "_f" in s.chp else self.default_font)
                try:
                    txt = b.decode(cp)
                except (LookupError, UnicodeDecodeError):
                    txt = b.decode("cp1252", "replace")
                self.text(s, txt)

        ucskip = 0
        for t in toks:
            if t.kind != "hex" and hexbuf:
                flush_hex(st)
            if ucskip:
                # characters after \uN that stand in for it
                if t.kind == "hex" or (t.kind == "sym" and t.word not in "{}\\"):
                    ucskip -= 1
                    continue
                if t.kind == "text":
                    txt = t.text
                    k = min(ucskip, len(txt))
                    ucskip -= k
                    txt = txt[k:]
                    if not txt:
                        continue
                    t = Tok("text", text=txt)
                elif t.kind == "cw":
                    ucskip = 0
                else:
                    ucskip = 0
            if t.kind == "{":
                stack.append(st)
                st = st.copy()
                self.on_open(st)
                continue
            if t.kind == "}":
                self.on_close(st)
                if not stack:
                    break
                prev = st
                st = stack.pop()
                self.after_close(prev, st)
                continue
            if st.skip and t.kind != "cw":
                continue
            if t.kind == "text":
                if st.dest in ("body",) or st.dest in self.TEXT_DESTS:
                    try:
                        txt = t.text.decode(self.charset(st.chp.get("_f", self.default_font)))
                    except (LookupError, UnicodeDecodeError):
                        txt = t.text.decode("cp1252", "replace")
                    self.text(st, txt)
                continue
            if t.kind == "hex":
                if st.dest in ("body",) or st.dest in self.TEXT_DESTS:
                    hexbuf.append(t.arg)
                continue
            if t.kind == "bin":
                self.on_bin(st, t.text)
                continue
            if t.kind == "sym":
                s = t.word
                if s == "*":
                    st.ignore_unknown = True
                    continue
                if st.skip:
                    continue
                if s in "\\{}":
                    self.text(st, s)
                elif s == "~":
                    self.text(st, "\u00a0")
                elif s == "_":
                    self.text(st, "\u2011")
                elif s == "-":
                    self.text(st, "\u00ad")
                elif s in "\r\n":
                    self.control(st, "par", None)
                elif s == "\t":
                    self.control(st, "tab", None)
                continue
            # control word
            w, a = t.word, t.arg
            if st.dest == "body" and not self.stories:
                self._cur_st = st
            if w == "u" and a is not None:
                if not st.skip and (st.dest == "body" or st.dest in self.TEXT_DESTS):
                    self.text(st, chr(a + 65536 if a < 0 else a))
                ucskip = st.uc
                continue
            if w == "uc":
                st.uc = a if a is not None else 1
                continue
            if st.skip:
                continue
            handled = self.control(st, w, a)
            if not handled and st.ignore_unknown and st.dest_fresh:
                st.skip = True
        self.finish()

    TEXT_DESTS = {"pict", "cell", "header", "note", "fldrslt", "fldinst", "fonttbl", "stylesheet",
                  "colortbl", "info_field", "leveltext", "levelnumbers", "annotation", "bkmk",
                  "listname", "docvar"}

    # opening a group: the next control word names its destination
    def on_open(self, st):
        st.ignore_unknown = False
        st.dest_fresh = True

    def text(self, st, txt):
        d = st.dest
        if d == "body":
            txt = txt.replace("\x00", "")
            if txt:
                self.add_text(st, txt)
        elif d == "fonttbl":
            while ";" in txt:
                head, txt = txt.split(";", 1)
                self._group_text.append(head)
                self._font_done()
            if txt:
                self._group_text.append(txt)
        elif d in ("stylesheet", "info_field", "leveltext", "levelnumbers", "bkmk",
                   "listname", "fldinst"):
            self._group_text.append(txt)
        elif d == "colortbl":
            if ";" in txt:
                for _ in range(txt.count(";")):
                    self._color_done()

    def _color_done(self):
        c = self._color
        self.colors.append("%02X%02X%02X" % (c[0], c[1], c[2]) if c[3] else None)
        self._color = [0, 0, 0, False]

    def on_bin(self, st, data):
        if st.dest == "pict":
            self._pict["bin"] = data

    # -------------------------------------------------------------- the big switch
    def control(self, st, w, a):
        fresh = getattr(st, "dest_fresh", False)
        st.dest_fresh = False
        # ---- destinations
        if fresh:
            if w in ("fonttbl", "colortbl", "stylesheet", "info", "listtable", "listoverridetable"):
                st.dest = w
                if w == "colortbl":
                    self._color = [0, 0, 0, False]
                return True
            if w in ("header", "headerl", "headerr", "headerf", "footer", "footerl", "footerr", "footerf"):
                kind = "headers" if w.startswith("header") else "footers"
                typ = {"": "default", "r": "default", "l": "even", "f": "first"}[w[6:] if kind == "headers" else w[6:]]
                self.push_story(st, "header")
                st.dest = "body"
                st.pap = _new_pap()
                st._hf = (kind, typ)
                return True
            if w in ("footnote",):
                self.push_story(st, "note")
                st.dest = "body"
                st.pap = _new_pap()
                st._note = "footnote"
                return True
            if w == "annotation":
                self.push_story(st, "annotation")
                st.dest = "body"
                st.pap = _new_pap()
                return True
            if w == "field":
                self.field_stack.append({"instr": [], "result": None, "runs_before": None,
                                         "lock": False})
                st.dest = "field"
                st._field = True
                return True
            if w == "fldinst":
                st.dest = "fldinst"
                self._group_text = []
                return True
            if w == "fldrslt":
                f = self.field_stack[-1] if self.field_stack else None
                if f is not None:
                    f["outer_runs"] = self.story.runs
                    self.story.runs = []
                st.dest = "body"
                st._fldrslt = True
                return True
            if w in ("pict",):
                self._pict = {"hex": [], "w": 0, "h": 0, "wg": 0, "hg": 0, "sx": 100, "sy": 100, "ext": None}
                st.dest = "pict"
                return True
            if w == "shppict":
                st.dest = "shppict"
                return True
            if w == "nonshppict":
                st.skip = True
                return True
            if w in ("bkmkstart", "bkmkend"):
                st.dest = "bkmk"
                st._bkmk = w
                self._group_text = []
                return True
            if w in ("atrfstart", "atrfend"):
                st.dest = "bkmk"
                st._bkmk = w
                self._group_text = []
                return True
            if w in ("atnid", "atnauthor", "atndate", "atnref"):
                st.dest = "info_field"
                st._atn = w
                self._group_text = []
                return True
            if w in ("title", "subject", "author", "keywords", "doccomm", "operator", "company"):
                if st.dest == "info":
                    st.dest = "info_field"
                    st._info = w
                    self._group_text = []
                    return True
            if w in ("list",) and st.dest == "listtable":
                self._list = {"levels": [], "id": None}
                st.dest = "list"
                return True
            if w == "listlevel" and st.dest == "list":
                self._lvl = {"start": 1, "fmt": "decimal", "text": "", "jc": "left", "ind": 0,
                             "hang": 0, "_nums": "", "_tmpl": []}
                st.dest = "listlevel"
                return True
            if w == "leveltext" and st.dest == "listlevel":
                st.dest = "leveltext"
                self._group_text = []
                return True
            if w == "levelnumbers" and st.dest == "listlevel":
                st.dest = "levelnumbers"
                self._group_text = []
                return True
            if w == "listoverride" and st.dest == "listoverridetable":
                self._lo = {"id": None, "ls": None, "starts": {}}
                st.dest = "listoverride"
                return True
            if w == "lfolevel" and st.dest == "listoverride":
                st.dest = "lfolevel"
                self._lfo_lvl = {"n": len(self._lo["starts"]), "start": None}
                return True
            if st.dest == "stylesheet" and w in ("cs", "ts", "ds", "s"):
                return self.c_style(st, w, a)
            if w == "nesttableprops":
                st._nest = True
                return True
            if w in SKIP or (st.ignore_unknown and w not in self.KNOWN_STAR):
                st.skip = True
                return True
        d = st.dest
        if d == "fonttbl":
            return self.c_font(st, w, a)
        if d == "colortbl":
            if w in ("red", "green", "blue"):
                self._color[{"red": 0, "green": 1, "blue": 2}[w]] = a or 0
                self._color[3] = True
            return True
        if d == "stylesheet":
            return self.c_style(st, w, a)
        if d in ("pict",):
            return self.c_pict(st, w, a)
        if d in ("list", "listlevel", "leveltext", "levelnumbers"):
            return self.c_list(st, w, a)
        if d in ("listoverride", "lfolevel"):
            return self.c_lo(st, w, a)
        if d in ("info", "info_field", "bkmk", "fldinst", "field", "shppict", "listtable",
                 "listoverridetable"):
            return True
        # ---- document setup
        if w == "ansicpg" and a:
            self.codepage = "cp%d" % a
            return True
        if w == "deff" and a is not None:
            self.default_font = a
            return True
        if w == "deftab" and a:
            self.deftab = a
            self.doc.tab_stop = a
            return True
        if w in ("paperw", "paperh", "margl", "margr", "margt", "margb", "gutter", "landscape",
                 "facingp", "titlepg"):
            key = {"paperw": "w", "paperh": "h", "margl": "left", "margr": "right", "margt": "top",
                   "margb": "bottom", "gutter": "gutter"}.get(w, w)
            self.doc_sec[key] = a if a is not None else True
            self.apply_doc_sec(self.sec)
            return True
        # ---- section
        if w == "sectd":
            self.sec_props = {}
            self.reset_sec(self.sec)
            return True
        if w in ("pgwsxn", "pghsxn", "marglsxn", "margrsxn", "margtsxn", "margbsxn", "guttersxn",
                 "headery", "footery", "cols", "colsx", "lndscpsxn", "titlepg", "sbknone", "sbkcol",
                 "sbkpage", "sbkeven", "sbkodd", "pgnrestart", "pgnstarts"):
            self.c_sect(w, a)
            return True
        if w == "sect":
            self.end_para_if_open(st)
            self.close_tables(0)
            self.new_section()
            return True
        # ---- paragraph
        if w == "pard":
            st.pap = _new_pap()
            if st.dest == "body" and not self.stories:
                self._open_para = st
            return True
        if w == "par":
            self.end_para(st)
            if not self.stories:
                self._open_para = None
            return True
        if w in ("ql", "qc", "qr", "qj", "qd", "qk0", "qk10", "qk20"):
            st.pap["ppr"]["align"] = {"ql": "left", "qc": "center", "qr": "right", "qj": "both",
                                     "qd": "distribute"}.get(w, "both")
            return True
        if w in ("li", "lin"):
            st.pap["ppr"]["ind_l"] = a or 0
            return True
        if w in ("ri", "rin"):
            st.pap["ppr"]["ind_r"] = a or 0
            return True
        if w == "fi":
            st.pap["ppr"]["ind_first"] = a or 0
            return True
        if w == "sb":
            st.pap["ppr"]["sb"] = a or 0
            return True
        if w == "sa":
            st.pap["ppr"]["sa"] = a or 0
            return True
        if w == "sl":
            if a:
                st.pap["ppr"]["line"] = abs(a)
                st.pap["ppr"]["line_rule"] = "exact" if a < 0 else "atLeast"
                st.pap["_slmult"] = True
            else:
                st.pap["ppr"].pop("line", None)
                st.pap["ppr"].pop("line_rule", None)
            return True
        if w == "slmult":
            if a == 1 and "line" in st.pap["ppr"]:
                st.pap["ppr"]["line_rule"] = "auto"
            return True
        if w == "keepn":
            st.pap["ppr"]["keep_next"] = a != 0
            return True
        if w == "keep":
            st.pap["ppr"]["keep_lines"] = a != 0
            return True
        if w == "pagebb":
            st.pap["ppr"]["pbb"] = a != 0
            return True
        if w == "widctlpar":
            st.pap["ppr"]["widow"] = True
            return True
        if w == "nowidctlpar":
            st.pap["ppr"]["widow"] = False
            return True
        if w == "contextualspace":
            st.pap["ppr"]["contextual"] = True
            return True
        if w == "rtlpar":
            st.pap["ppr"]["bidi"] = True
            return True
        if w == "outlinelevel":
            st.pap["ppr"]["outline"] = a or 0
            return True
        if w == "s":
            st.pap["style"] = self.styles.get(a or 0)
            return True
        if w == "ls":
            st.pap["ls"] = a
            return True
        if w == "ilvl":
            st.pap["ilvl"] = a or 0
            return True
        if w == "intbl":
            st.pap["intbl"] = True
            if not st.pap["itap"]:
                st.pap["itap"] = 1
            return True
        if w == "itap":
            st.pap["itap"] = a or 0
            st.pap["intbl"] = bool(a)
            return True
        if w in ("tqr", "tqc", "tqdec", "tb") or w in TAB_LEADERS:
            pend = st.pap.setdefault("_tab", {})
            if w in TAB_LEADERS:
                pend["leader"] = TAB_LEADERS[w]
            else:
                pend["kind"] = {"tqr": "right", "tqc": "center", "tqdec": "decimal", "tb": "bar"}[w]
                if w == "tb" and a is not None:
                    self._add_tab(st, a)
            return True
        if w == "tx" and a is not None:
            self._add_tab(st, a)
            return True
        if w in ("brdrt", "brdrb", "brdrl", "brdrr", "brdrbtw", "box"):
            st.pap["_brd"] = {"brdrt": "top", "brdrb": "bottom", "brdrl": "left", "brdrr": "right",
                              "brdrbtw": "between", "box": "box"}[w]
            st.pap["ppr"].setdefault("borders", {})
            self._brd_set(st.pap["ppr"]["borders"], st.pap["_brd"], kind="single")
            st._brdtarget = ("para", st.pap["_brd"])
            return True
        if w in BORDERS or w in ("brdrw", "brsp", "brdrcf"):
            tgt = getattr(st, "_brdtarget", None)
            if tgt is None:
                return True
            if tgt[0] == "para":
                bd = st.pap["ppr"].setdefault("borders", {})
                self._brd_set(bd, tgt[1], **self._brd_arg(w, a))
            elif tgt[0] == "cell":
                bd = self._rowdef_cell().setdefault("borders", {})
                self._brd_set(bd, tgt[1], **self._brd_arg(w, a))
            elif tgt[0] == "row":
                self._rowdef()["tborders"] = True
            return True
        if w in ("cbpat", "shading", "cfpat") and not getattr(st, "_in_cell_def", False):
            if w == "cbpat" and a and a < len(self.colors) and self.colors[a]:
                st.pap["ppr"]["shd"] = self.colors[a]
            return True
        # ---- character
        if w == "deleted":
            st.chp["_del"] = a != 0
            return True
        if w in ("revised", "revauth", "revauthdel", "revdttm", "revdttmdel", "crauth", "crdate"):
            return True
        if w == "plain":
            st.chp = {}
            st.cstyle = None
            return True
        if w in ("b", "i", "strike", "caps", "scaps", "v", "outl", "shad", "embo", "impr", "striked"):
            key = {"b": "b", "i": "i", "strike": "strike", "caps": "caps", "scaps": "smallcaps",
                   "v": "hidden", "outl": "outline", "shad": "shadow", "embo": "emboss",
                   "impr": "imprint", "striked": "dstrike"}[w]
            st.chp[key] = a != 0
            return True
        if w in UNDERLINES:
            if a == 0:
                st.chp["u"] = False
            else:
                st.chp["u"] = UNDERLINES[w]
            return True
        if w == "ulnone":
            st.chp["u"] = False
            return True
        if w == "f" and a is not None:
            st.chp["_f"] = a
            return True
        if w in ("af", "dbch", "hich", "loch", "rtlch", "ltrch", "afs"):
            return True
        if w == "fs":
            st.chp["sz"] = a or 24
            return True
        if w == "cf":
            c = self.colors[a] if a is not None and a < len(self.colors) else None
            if c:
                st.chp["color"] = c
            else:
                st.chp.pop("color", None)
            return True
        if w == "highlight":
            if a and a in HIGHLIGHT:
                st.chp["highlight"] = HIGHLIGHT[a]
            else:
                st.chp.pop("highlight", None)
            return True
        if w in ("cb", "chcbpat"):
            c = self.colors[a] if a is not None and a < len(self.colors) else None
            if c:
                st.chp["shd"] = c
            return True
        if w == "super":
            st.chp["vert"] = "superscript"
            return True
        if w == "sub":
            st.chp["vert"] = "subscript"
            return True
        if w == "nosupersub":
            st.chp.pop("vert", None)
            return True
        if w == "up":
            st.chp["position"] = a or 6
            return True
        if w == "dn":
            st.chp["position"] = -(a or 6)
            return True
        if w == "expndtw":
            st.chp["spacing"] = a or 0
            return True
        if w == "expnd":
            st.chp["spacing"] = (a or 0) * 5
            return True
        if w == "charscalex":
            st.chp["scale"] = a or 100
            return True
        if w in ("lang", "langnp"):
            tag = LCID.get(a or 0)
            if tag:
                st.chp["lang"] = tag
            return True
        if w == "cs":
            st.cstyle = self.styles.get("c%d" % (a or 0))
            return True
        # ---- special characters
        if w in ("line", "lbr"):
            self.add_run(st, "br")
            return True
        if w == "tab":
            self.add_run(st, "tab")
            return True
        if w == "page":
            self.add_run(st, "page")
            return True
        if w == "column":
            self.add_run(st, "col")
            return True
        if w in SYMBOLS:
            self.text(st, SYMBOLS[w])
            return True
        if w == "chftn" and st.dest == "note":
            return True
        if w == "ftnalt":
            st._note = "endnote"
            return True
        # ---- tables
        if w == "trowd":
            self._rd_depth = max(2, st.pap["itap"]) if getattr(st, "_nest", False) else 1
            self._rowdef_new()
            return True
        if w in ("trgaph", "trleft", "trqc", "trqr", "trql", "trrh", "trhdr", "trkeep",
                 "trautofit"):
            rd = self._rowdef()
            if w == "trgaph":
                rd["gap"] = a or 0
            elif w == "trleft":
                rd["left"] = a or 0
            elif w in ("trqc", "trqr", "trql"):
                rd["align"] = {"trqc": "center", "trqr": "right", "trql": None}[w]
            elif w == "trrh":
                rd["height"] = a or 0
            elif w == "trhdr":
                rd["header"] = True
            elif w == "trkeep":
                rd["cant_split"] = True
            return True
        if w in ("trbrdrt", "trbrdrb", "trbrdrl", "trbrdrr", "trbrdrh", "trbrdrv"):
            st._brdtarget = ("row", w)
            self._rowdef()["tborders"] = True
            return True
        if w in ("clbrdrt", "clbrdrb", "clbrdrl", "clbrdrr"):
            side = {"clbrdrt": "top", "clbrdrb": "bottom", "clbrdrl": "left", "clbrdrr": "right"}[w]
            st._brdtarget = ("cell", side)
            bd = self._rowdef_cell().setdefault("borders", {})
            self._brd_set(bd, side, kind="single")
            return True
        if w in ("clvmgf", "clvmrg", "clmgf", "clmrg"):
            c = self._rowdef_cell()
            if w == "clvmgf":
                c["vmerge"] = "restart"
            elif w == "clvmrg":
                c["vmerge"] = "cont"
            elif w == "clmgf":
                c["hmerge"] = "first"
            else:
                c["hmerge"] = "cont"
            return True
        if w in ("clcbpat", "clcbpatraw"):
            if a and a < len(self.colors) and self.colors[a]:
                self._rowdef_cell()["shd"] = self.colors[a]
            return True
        if w in ("clvertalt", "clvertalc", "clvertalb"):
            self._rowdef_cell()["valign"] = {"clvertalt": "top", "clvertalc": "center", "clvertalb": "bottom"}[w]
            return True
        if w == "cellx":
            rd = self._rowdef()
            c = self._rowdef_cell()
            c["x"] = a or 0
            rd["cells"].append(c)
            rd["_next"] = {}
            return True
        if w == "cell":
            self.end_cell(st, 1)
            return True
        if w == "nestcell":
            self.end_cell(st, max(2, st.pap["itap"]))
            return True
        if w == "row":
            self._rd_depth = 1
            self.end_row(1, self._rowdef_done(1))
            return True
        if w == "nestrow":
            d = max(2, st.pap["itap"])
            self.end_row(d, self._rowdef_done(d))
            return True
        if w == "nesttableprops":
            return True
        # ---- pictures sizes in a \pict group are handled in c_pict
        return False

    KNOWN_STAR = {"shppict", "fldinst", "bkmkstart", "bkmkend", "atnid", "atnauthor", "atndate",
                  "annotation", "atrfstart", "atrfend", "listtable", "listoverridetable",
                  "nesttableprops", "atnref"}

    def _add_tab(self, st, pos):
        pend = st.pap.pop("_tab", {})
        tabs = st.pap["ppr"].setdefault("tabs", [])
        tabs.append((pos, pend.get("kind", "left"), pend.get("leader")))

    def _brd_arg(self, w, a):
        if w in BORDERS:
            return {"kind": BORDERS[w]}
        if w == "brdrw":
            return {"sz": max(2, int(round((a or 10) * 8 / 20.0)))}
        if w == "brsp":
            return {"space": int((a or 0) / 20)}
        if w == "brdrcf":
            c = self.colors[a] if a is not None and a < len(self.colors) else None
            return {"color": c or "auto"}
        return {}

    def _brd_set(self, bd, side, kind=None, sz=None, color=None, space=None):
        sides = ("top", "left", "bottom", "right") if side == "box" else (side,)
        for s in sides:
            cur = list(bd.get(s, (4, "auto", "single", 0)))
            if sz is not None:
                cur[0] = sz
            if color is not None:
                cur[1] = color
            if kind is not None:
                cur[2] = kind
            if space is not None:
                cur[3] = space
            if cur[2] == "nil":
                bd.pop(s, None)
            else:
                bd[s] = tuple(cur)

    # row definitions (\trowd ... \cellx)
    def _rowdef_new(self):
        self._rds = getattr(self, "_rds", {})
        self._rds[getattr(self, "_rd_depth", 1)] = {"cells": [], "_next": {}, "left": 0}

    def _rowdef(self):
        self._rds = getattr(self, "_rds", {})
        d = getattr(self, "_rd_depth", 1)
        if d not in self._rds:
            self._rowdef_new()
        return self._rds[d]

    def _rowdef_cell(self):
        return self._rowdef().setdefault("_next", {})

    def _rowdef_done(self, depth=1):
        rd = getattr(self, "_rds", {}).get(depth)
        if rd is None:
            return None
        rd = dict(rd)
        rd.pop("_next", None)
        return rd

    def end_para_if_open(self, st):
        if self.story.runs:
            self.end_para(st)

    # -------------------------------------------------------------- font / style tables
    def c_font(self, st, w, a):
        if w == "f" and a is not None:
            self._font = {"n": a, "charset": 0}
            self._group_text = []
        elif w == "fcharset" and hasattr(self, "_font"):
            self._font["charset"] = a or 0
        return True

    def _font_done(self):
        f = getattr(self, "_font", None)
        if f is not None:
            name = "".join(self._group_text).strip()
            if name and f["n"] not in self.fonts:
                self.fonts[f["n"]] = (name, CHARSETS.get(f["charset"], "cp1252"))
        self._group_text = []
        self._font = None

    def c_style(self, st, w, a):
        cur = st.__dict__.get("_style")
        if cur is None:
            cur = {"kind": "paragraph", "n": 0, "based": None, "next": None, "chp": {}, "pap": None}
            st._style = cur
            st.pap = _new_pap()
            st.chp = {}
            self._group_text = []
        if w == "s":
            cur["kind"], cur["n"] = "paragraph", a or 0
        elif w == "cs":
            cur["kind"], cur["n"] = "character", a or 0
        elif w == "ts":
            cur["kind"], cur["n"] = "table", a or 0
        elif w == "ds":
            cur["kind"], cur["n"] = "section", a or 0
        elif w == "sbasedon":
            cur["based"] = a
        elif w == "snext":
            cur["next"] = a
        elif w in ("additive", "sautoupd", "sqformat", "spriority", "ssemihidden", "sunhideused",
                   "slocked", "slink", "styrsid", "shidden", "spersonal", "scompose", "sreply"):
            pass
        else:
            st.dest = "body"
            self.control(st, w, a)
            st.dest = "stylesheet"
        return True

    # -------------------------------------------------------------- lists
    def c_list(self, st, w, a):
        if st.dest == "list":
            if w == "listid":
                self._list["id"] = a
            return True
        lv = self._lvl
        if w == "levelnfc" or w == "levelnfcn":
            lv["fmt"] = NFC.get(a or 0, "decimal")
        elif w == "levelstartat":
            lv["start"] = a if a is not None else 1
        elif w == "leveljc" or w == "leveljcn":
            lv["jc"] = {0: "left", 1: "center", 2: "right"}.get(a or 0, "left")
        elif w == "li":
            lv["ind"] = a or 0
        elif w == "fi":
            lv["hang"] = -(a or 0)
        elif w == "f" and a is not None:
            lv["_font"] = a
        elif st.dest == "leveltext" and w == "u" and a is not None:
            pass
        return True

    def c_lo(self, st, w, a):
        if st.dest == "listoverride":
            if w == "listid":
                self._lo["id"] = a
            elif w == "ls":
                self._lo["ls"] = a
            return True
        if w == "levelstartat":
            self._lfo_lvl["start"] = a
        return True

    # -------------------------------------------------------------- pictures
    def c_pict(self, st, w, a):
        p = self._pict
        if w in ("pngblip", "jpegblip", "emfblip", "wmetafile", "dibitmap", "wbitmap", "macpict",
                 "pmmetafile"):
            p["ext"] = {"pngblip": "png", "jpegblip": "jpg", "emfblip": "emf", "wmetafile": "wmf",
                        "dibitmap": "bmp", "wbitmap": "bmp", "macpict": "pict", "pmmetafile": "wmf"}[w]
        elif w in ("picw", "pich", "picwgoal", "pichgoal", "picscalex", "picscaley"):
            p[{"picw": "w", "pich": "h", "picwgoal": "wg", "pichgoal": "hg", "picscalex": "sx",
               "picscaley": "sy"}[w]] = a or 0
        return True

    # -------------------------------------------------------------- stories
    def push_story(self, st, kind):
        self.stories.append((self.story, kind))
        self.story = Story([])
        st._story_owner = kind

    def pop_story(self):
        story = self.story
        prev, kind = self.stories.pop()
        self.story = prev
        return story

    def _finish_story(self, st):
        """End of a header / note / comment group: its last paragraph and tables."""
        if self.story.runs:
            self.end_para(st)
        self.close_tables(0)
        return self.pop_story()

    def on_close(self, st):
        d = st.dest
        if d == "fonttbl":
            self._font_done()
        elif d == "stylesheet" and st.__dict__.get("_style") is not None:
            self._style_done(st)
        elif d == "info_field":
            txt = "".join(self._group_text).strip()
            key = getattr(st, "_info", None)
            if key:
                m = {"title": "title", "subject": "subject", "author": "creator",
                     "keywords": "keywords", "doccomm": "description"}.get(key)
                if m and txt:
                    self.doc.meta[m] = txt
            atn = getattr(st, "_atn", None)
            if atn:
                self._atn_pending = getattr(self, "_atn_pending", {})
                self._atn_pending[atn] = txt
        elif d == "bkmk":
            name = "".join(self._group_text).strip()
            kind = getattr(st, "_bkmk", "")
            if name:
                if kind == "bkmkstart":
                    self.story.runs.append({"t": "bmstart", "name": name})
                elif kind == "bkmkend":
                    self.story.runs.append({"t": "bmend", "name": name})
                elif kind == "atrfstart":
                    cid = self.comments.setdefault(name, len(self.comments))
                    self.story.runs.append({"t": "cstart", "id": cid})
                elif kind == "atrfend":
                    cid = self.comments.setdefault(name, len(self.comments))
                    self.story.runs.append({"t": "_cend", "id": cid})
        elif d == "fldinst":
            if self.field_stack:
                self.field_stack[-1]["instr"].append("".join(self._group_text))
            self._group_text = []
        elif d == "pict":
            self._pict_done(st)
        elif d == "listlevel":
            self._lvl_done()
        elif d == "list":
            self._list_done()
        elif d == "listoverride":
            self._lo_done()
        elif d == "lfolevel":
            if self._lfo_lvl.get("start") is not None:
                self._lo["starts"][self._lfo_lvl["n"]] = self._lfo_lvl["start"]
        elif d == "leveltext":
            self._lvl["_tmpl"] = list(self._group_text)
        elif d == "levelnumbers":
            self._lvl["_nums"] = "".join(self._group_text)
        elif d == "colortbl":
            pass

    def after_close(self, closed, st):
        owner = closed.__dict__.get("_story_owner")
        if owner:
            story = self._finish_story(closed)
            if owner == "header":
                kind, typ = closed._hf
                self.sec[kind][typ] = story.blocks
            elif owner == "note":
                self.story.runs.append({"t": "note", "kind": getattr(closed, "_note", "footnote"),
                                        "blocks": story.blocks or [B.para()],
                                        "rpr": self.run_props(st)})
            elif owner == "annotation":
                pend = getattr(self, "_atn_pending", {}) or {}
                ref = pend.get("atnref") or pend.get("atnid")
                cid = None
                if pend.get("atnref") and pend["atnref"] in self.comments:
                    cid = self.comments[pend["atnref"]]
                if cid is None:
                    cid = len(self.comments)
                    self.comments["_anon%d" % cid] = cid
                author = pend.get("atnauthor") or pend.get("atnid") or "Author"
                self.doc.comments.append({"id": cid, "author": author,
                                          "initials": pend.get("atnid") or "", "date": "",
                                          "blocks": story.blocks or [B.para()]})
                # the comment mark: the range ends here (or at \atrfend)
                runs = self.story.runs
                ends = [r for r in runs if r.get("t") == "_cend" and r["id"] == cid]
                if ends:
                    for r in ends:
                        r["t"] = "cend"
                else:
                    if not any(r.get("t") == "cstart" and r.get("id") == cid for r in runs):
                        runs.append({"t": "cstart", "id": cid})
                    runs.append({"t": "cend", "id": cid})
                self._atn_pending = {}
                del ref
        if closed.__dict__.get("_fldrslt"):
            f = self.field_stack[-1] if self.field_stack else None
            if f is not None:
                f["result"] = self.story.runs
                self.story.runs = f.pop("outer_runs", [])
        if closed.__dict__.get("_field") and self.field_stack:
            f = self.field_stack.pop()
            self._field_done(st, f)

    def _field_done(self, st, f):
        instr = "".join(f["instr"]).strip()
        result = f["result"] or []
        m = re.match(r'HYPERLINK\s+(?:\\l\s+"([^"]*)"|"([^"]*)"|(\S+))(.*)$', instr, re.S | re.I)
        if m:
            anchor = m.group(1)
            url = m.group(2) or m.group(3)
            rest = m.group(4) or ""
            m2 = re.search(r'\\l\s+"([^"]*)"', rest)
            if m2 and not anchor:
                anchor = m2.group(1)
            run = {"t": "link", "runs": result}
            if anchor and not url:
                run["anchor"] = anchor
            else:
                run["url"] = url or ""
                if anchor:
                    run["url"] += "#" + anchor
            self.story.runs.append(run)
            return
        if not instr:
            self.story.runs.extend(result)
            return
        self.story.runs.append({"t": "field", "instr": instr, "result": result,
                                "rpr": result[0].get("rpr", {}) if result else self.run_props(st)})

    def _style_done(self, st):
        cur = st._style
        name = "".join(self._group_text).strip().rstrip(";").strip()
        self._group_text = []
        st._style = None
        if not name:
            return
        kind = cur["kind"]
        if kind == "section":
            return
        # Word writes built-in names in lower case ("heading 1"): the canonical name and id
        canon = {k.lower(): k for k in B.BUILTIN}.get(name.lower())
        if canon:
            name = canon
        sid = B.style_id(name)
        if any(s["id"] == sid and s["type"] != kind for s in self.doc.styles):
            sid = sid + ("Char" if kind == "character" else "Table" if kind == "table" else "Para")
        key = cur["n"] if kind == "paragraph" else ("c%d" if kind == "character" else "t%d") % cur["n"]
        self.styles[key] = sid
        chp = self.run_props(st)
        pap = dict(st.pap["ppr"])
        if st.pap["ls"] is not None:
            pap["_ls"] = (st.pap["ls"], st.pap["ilvl"])
        self._raw_styles = getattr(self, "_raw_styles", [])
        self._raw_styles.append((sid, name, kind, cur["based"], cur["next"], pap, chp))

    def _resolve_styles(self):
        for sid, name, kind, based, nxt, pap, chp in getattr(self, "_raw_styles", []):
            bkey = based if kind == "paragraph" else ("c%d" % based if kind == "character" else "t%d" % based) \
                if based is not None else None
            nkey = nxt if kind == "paragraph" else None
            b = self.styles.get(bkey) if bkey is not None else None
            n = self.styles.get(nkey) if nkey is not None else None
            ls = pap.pop("_ls", None)
            if ls and ls[0] in self.ls:
                pap["num"] = (self.ls[ls[0]], ls[1])
            self.doc.add_style(sid, name, kind, based=b if b != sid else None, nxt=n,
                               ppr=pap if kind == "paragraph" else {}, rpr=chp,
                               default=(kind == "paragraph" and name == "Normal"))

    def _pict_done(self, st):
        p = self._pict
        if p.get("bin") is not None:
            data = p["bin"]
        else:
            hx = "".join(p.get("_hex", []))
            data = b""
        if not data:
            # hex digits came as text
            raw = getattr(self, "_pict_text", None)
            data = raw or b""
        if not data or not p.get("ext"):
            return
        if p["ext"] == "bmp" and not data.startswith(b"BM"):
            return
        wg, hg = p["wg"], p["hg"]
        if not wg and p["w"]:
            wg = p["w"] * 1440 // 2540 if p["ext"] in ("emf", "wmf") else p["w"] * 15
        if not hg and p["h"]:
            hg = p["h"] * 1440 // 2540 if p["ext"] in ("emf", "wmf") else p["h"] * 15
        wg = wg * p["sx"] // 100
        hg = hg * p["sy"] // 100
        if wg <= 0 or hg <= 0:
            wg, hg = 2880, 2160
        run = {"t": "image", "data": data, "ext": p["ext"], "cx": wg * B.EMU_PER_TWIP,
               "cy": hg * B.EMU_PER_TWIP, "rpr": {}}
        self.story.runs.append(run)

    def _lvl_done(self):
        lv = self._lvl
        tmpl = "".join(lv.pop("_tmpl", []))
        nums = lv.pop("_nums", "")
        font = lv.pop("_font", None)
        text = ""
        if tmpl:
            # \leveltext: first char is the length, then the text with level-number placeholders
            t = tmpl
            count = ord(t[0]) if t else 0
            body = t[1:1 + count] if count else t[1:]
            places = [ord(c) for c in nums]
            out = []
            for i, ch in enumerate(body, 1):
                if i in places:
                    out.append("%%%d" % (ord(ch) + 1))
                else:
                    out.append(ch)
            text = "".join(out)
        if lv["fmt"] == "bullet":
            lv["bullet"] = text or "\u2022"
            text = text or "\u2022"
        lv["text"] = text
        if font is not None and font in self.fonts:
            lv["font"] = self.fonts[font][0]
        self._list["levels"].append(lv)

    def _list_done(self):
        levels = self._list["levels"][:9]
        while len(levels) < 9:
            i = len(levels)
            levels.append({"fmt": "decimal", "text": "%%%d." % (i + 1), "ind": 720 * (i + 1), "hang": 360,
                           "start": 1, "jc": "left"})
        for i, lv in enumerate(levels):
            if not lv.get("ind"):
                lv["ind"] = 720 * (i + 1)
            if not lv.get("hang"):
                lv["hang"] = 360
        self.doc.lists.append(levels)
        if self._list["id"] is not None:
            self.lists[self._list["id"]] = len(self.doc.lists) - 1

    def _lo_done(self):
        lo = self._lo
        if lo["id"] not in self.lists or lo["ls"] is None:
            return
        idx = self.lists[lo["id"]]
        restart = False
        if lo["starts"]:
            levels = [dict(l) for l in self.doc.lists[idx]]
            for i, s in lo["starts"].items():
                if i < 9:
                    levels[i]["start"] = s
            self.doc.lists.append(levels)
            idx = len(self.doc.lists) - 1
            restart = True
        self.doc.nums.append((idx, restart))
        self.ls[lo["ls"]] = len(self.doc.nums) - 1

    # -------------------------------------------------------------- sections
    def apply_doc_sec(self, s):
        d = self.doc_sec
        for k in ("w", "h", "landscape"):
            if k in d:
                s[k] = d[k]
        for k in ("left", "right", "top", "bottom", "gutter"):
            if k in d:
                s["margins"][k] = d[k]
        if d.get("titlepg"):
            s["title_pg"] = True

    def reset_sec(self, s):
        fresh = B.section()
        for k in ("w", "h", "landscape", "margins", "title_pg", "cols", "col_space", "break"):
            s[k] = fresh[k]
        self.apply_doc_sec(s)

    def c_sect(self, w, a):
        s = self.sec
        if w == "pgwsxn":
            s["w"] = a
        elif w == "pghsxn":
            s["h"] = a
        elif w in ("marglsxn", "margrsxn", "margtsxn", "margbsxn", "guttersxn"):
            s["margins"][{"marglsxn": "left", "margrsxn": "right", "margtsxn": "top",
                          "margbsxn": "bottom", "guttersxn": "gutter"}[w]] = a or 0
        elif w == "headery":
            s["margins"]["header"] = a or 720
        elif w == "footery":
            s["margins"]["footer"] = a or 720
        elif w == "cols":
            s["cols"] = max(1, a or 1)
        elif w == "colsx":
            s["col_space"] = a or 720
        elif w == "lndscpsxn":
            s["landscape"] = True
        elif w == "titlepg":
            s["title_pg"] = True
        elif w in ("sbknone", "sbkcol", "sbkpage", "sbkeven", "sbkodd"):
            s["break"] = {"sbknone": "continuous", "sbkcol": "nextColumn", "sbkpage": "nextPage",
                          "sbkeven": "evenPage", "sbkodd": "oddPage"}[w]
        elif w == "pgnstarts":
            s["page_start"] = a or 1

    def new_section(self):
        self.doc.sections.append(self.sec)
        nxt = B.section()
        # a new section takes the previous one's setup until \sectd says otherwise
        for k in ("w", "h", "landscape", "cols", "col_space", "title_pg"):
            nxt[k] = self.sec[k]
        nxt["margins"] = dict(self.sec["margins"])
        nxt["headers"] = {}
        nxt["footers"] = {}
        self.sec = nxt
        self.story.blocks = nxt["blocks"]

    def finish(self):
        st = getattr(self, "_open_para", None) or getattr(self, "_cur_st", None) or State()
        if st.pap.get("intbl") and not self.story.runs:
            st = None
        if st is not None and self.story.runs:
            # text after the last \par: a last paragraph (an empty one after it is the
            # document's own end, as Word reads it)
            self.end_para(st)
        self.close_tables(0)
        self.doc.sections.append(self.sec)
        # a section's header continues from the one before when it has none (Word's linking)
        prev_h, prev_f = {}, {}
        for s in self.doc.sections:
            for typ, blk in prev_h.items():
                s["headers"].setdefault(typ, blk)
            for typ, blk in prev_f.items():
                s["footers"].setdefault(typ, blk)
            prev_h, prev_f = s["headers"], s["footers"]
        self._resolve_styles()
        if not self.doc.style("Normal"):
            self.doc.add_style("Normal", "Normal", default=True)
        # default font and size: from \deff and the Normal style
        dfont = self.fonts.get(self.default_font)
        if dfont:
            self.doc.defaults["rpr"].setdefault("font", dfont[0])
        self.doc.defaults["rpr"].setdefault("sz", 24)
        # comment ends that never got their comment
        for b in self.doc.all_blocks():
            for r in b.get("runs", []):
                if r.get("t") == "_cend":
                    r["t"] = "cend"
        return self.doc


class _HexCollector(Reader):
    pass


def read_bytes(data):
    """An RTF file's bytes as a document model."""
    if not data.lstrip()[:5].startswith(b"{\\rtf"):
        raise ValueError("This isn't an RTF file.")
    r = Reader(data)
    r.text_orig = r.text

    # pictures: hex digits arrive as text in the \pict destination
    def text(st, txt):
        if st.dest == "pict":
            r._pict_hex.append(txt)
            return
        r.text_orig(st, txt)
    r.text = text
    r._pict_hex = []
    orig_close = r.on_close

    def on_close(st):
        if st.dest == "pict":
            hx = re.sub(r"[^0-9a-fA-F]", "", "".join(r._pict_hex))
            r._pict_hex = []
            if len(hx) % 2:
                hx = hx[:-1]
            try:
                r._pict_text = bytes.fromhex(hx)
            except ValueError:
                r._pict_text = b""
        orig_close(st)
        if st.dest == "pict":
            r._pict_text = None
    r.on_close = on_close
    r.run()
    return r.doc


def read(path):
    with open(path, "rb") as fh:
        return read_bytes(fh.read())
