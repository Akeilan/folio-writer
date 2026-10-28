"""A .docx package read into the shared document model (docxbuild.Doc), so it can be
written in other formats (OpenDocument text)."""
import posixpath
import zipfile
import xml.etree.ElementTree as ET

from . import docxbuild as B

W = "{%s}" % B.W_NS
R = "{%s}" % B.R_NS
NSM = {"w": B.W_NS, "r": B.R_NS,
       "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
       "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
       "pic": "http://schemas.openxmlformats.org/drawingml/2006/picture",
       "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
       "v": "urn:schemas-microsoft-com:vml",
       "wps": "http://schemas.microsoft.com/office/word/2010/wordprocessingShape"}
WP = "{%s}" % NSM["wp"]
A_ = "{%s}" % NSM["a"]
MC = "{%s}" % NSM["mc"]
REL_NS = "{http://schemas.openxmlformats.org/package/2006/relationships}"


def wv(el, default=None):
    if el is None:
        return default
    return el.get(W + "val", default)


def on(el):
    """A w:b / w:i style toggle."""
    if el is None:
        return None
    v = el.get(W + "val")
    return v not in ("0", "false", "off", "none")


def num(v, default=0):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return default


class Reader:
    def __init__(self, path):
        self.z = zipfile.ZipFile(path)
        self.names = set(self.z.namelist())
        self.doc = B.Doc()
        self.theme_fonts = {}
        self.comment_map = {}

    def xml(self, name):
        if name not in self.names:
            return None
        return ET.fromstring(self.z.read(name))

    def rels(self, part):
        d, f = posixpath.split(part)
        rp = posixpath.join(d, "_rels", f + ".rels")
        out = {}
        root = self.xml(rp)
        if root is None:
            return out
        for r in root:
            tgt = r.get("Target", "")
            if r.get("TargetMode") != "External":
                tgt = posixpath.normpath(posixpath.join(d, tgt)) if not tgt.startswith("/") else tgt.lstrip("/")
            out[r.get("Id")] = (r.get("Type", "").rsplit("/", 1)[-1], tgt, r.get("TargetMode") == "External")
        return out

    # ---------------------------------------------------------------- props
    def rpr(self, el):
        r = {}
        if el is None:
            return r
        for ch in el:
            t = ch.tag[len(W):] if ch.tag.startswith(W) else None
            if t is None:
                continue
            if t == "rFonts":
                f = ch.get(W + "ascii") or ch.get(W + "hAnsi")
                th = ch.get(W + "asciiTheme") or ch.get(W + "hAnsiTheme")
                if not f and th:
                    f = self.theme_fonts.get("major" if th.startswith("major") else "minor")
                if f:
                    r["font"] = f
                ea = ch.get(W + "eastAsia")
                if ea:
                    r["font_ea"] = ea
                cs = ch.get(W + "cs")
                if cs:
                    r["font_cs"] = cs
            elif t in ("b", "i", "caps", "smallCaps", "strike", "dstrike", "outline", "shadow",
                       "emboss", "imprint", "vanish"):
                key = {"smallCaps": "smallcaps", "vanish": "hidden"}.get(t, t)
                r[key] = on(ch)
            elif t == "sz":
                r["sz"] = num(wv(ch), 22)
            elif t == "color":
                c = wv(ch)
                if c and c != "auto":
                    r["color"] = c.upper()
            elif t == "u":
                r["u"] = wv(ch, "single")
            elif t == "highlight":
                r["highlight"] = wv(ch)
            elif t == "shd":
                f = ch.get(W + "fill")
                if f and f != "auto":
                    r["shd"] = f.upper()
            elif t == "vertAlign":
                r["vert"] = wv(ch)
            elif t == "spacing":
                r["spacing"] = num(wv(ch))
            elif t == "w":
                r["scale"] = num(wv(ch), 100)
            elif t == "position":
                r["position"] = num(wv(ch))
            elif t == "lang":
                if wv(ch):
                    r["lang"] = wv(ch)
            elif t == "rStyle":
                r["_cstyle"] = wv(ch)
        return r

    def ppr(self, el):
        p = {}
        if el is None:
            return p
        for ch in el:
            t = ch.tag[len(W):] if ch.tag.startswith(W) else None
            if t == "jc":
                v = wv(ch, "left")
                p["align"] = {"start": "left", "end": "right"}.get(v, v)
            elif t == "spacing":
                if ch.get(W + "before") is not None:
                    p["sb"] = num(ch.get(W + "before"))
                if ch.get(W + "after") is not None:
                    p["sa"] = num(ch.get(W + "after"))
                if ch.get(W + "line") is not None:
                    p["line"] = num(ch.get(W + "line"), 240)
                    p["line_rule"] = ch.get(W + "lineRule", "auto")
            elif t == "ind":
                l = ch.get(W + "left") or ch.get(W + "start")
                rr = ch.get(W + "right") or ch.get(W + "end")
                if l is not None:
                    p["ind_l"] = num(l)
                if rr is not None:
                    p["ind_r"] = num(rr)
                if ch.get(W + "hanging") is not None:
                    p["ind_first"] = -num(ch.get(W + "hanging"))
                elif ch.get(W + "firstLine") is not None:
                    p["ind_first"] = num(ch.get(W + "firstLine"))
            elif t == "keepNext":
                p["keep_next"] = on(ch)
            elif t == "keepLines":
                p["keep_lines"] = on(ch)
            elif t == "pageBreakBefore":
                p["pbb"] = on(ch)
            elif t == "widowControl":
                p["widow"] = on(ch)
            elif t == "contextualSpacing":
                p["contextual"] = on(ch)
            elif t == "outlineLvl":
                lv = num(wv(ch), 9)
                if lv < 9:
                    p["outline"] = lv
            elif t == "numPr":
                ilvl = num(wv(ch.find(W + "ilvl")), 0)
                nid = num(wv(ch.find(W + "numId")), 0)
                p["_numid"] = (nid, ilvl)
            elif t == "shd":
                f = ch.get(W + "fill")
                if f and f != "auto":
                    p["shd"] = f.upper()
            elif t == "pBdr":
                b = {}
                for side in ch:
                    s = side.tag[len(W):]
                    if wv(side) in (None, "nil", "none"):
                        continue
                    b[s] = (num(side.get(W + "sz"), 4), (side.get(W + "color") or "000000").replace("auto", "000000"),
                            wv(side), num(side.get(W + "space"), 0))
                if b:
                    p["borders"] = b
            elif t == "tabs":
                tabs = []
                for tb in ch:
                    if wv(tb) == "clear":
                        continue
                    tabs.append((num(tb.get(W + "pos")), wv(tb, "left"), tb.get(W + "leader")))
                p["tabs"] = tabs
            elif t == "bidi":
                p["bidi"] = on(ch)
            elif t == "pStyle":
                p["_style"] = wv(ch)
            elif t == "rPr":
                p["_mark"] = self.rpr(ch)
            elif t == "sectPr":
                p["_sect"] = ch
        return p

    # -------------------------------------------------------------- tables
    def read_theme(self):
        th = self.xml("word/theme/theme1.xml")
        if th is None:
            return
        for kind in ("major", "minor"):
            el = th.find(".//%s%sFont/%slatin" % (A_, kind, A_))
            if el is not None and el.get("typeface"):
                self.theme_fonts[kind] = el.get("typeface")

    def read_styles(self):
        root = self.xml("word/styles.xml")
        d = self.doc
        if root is None:
            d.add_style("Normal", "Normal", default=True)
            return
        dd = root.find(W + "docDefaults")
        if dd is not None:
            d.defaults["rpr"] = self.rpr(dd.find(W + "rPrDefault/" + W + "rPr"))
            d.defaults["ppr"] = {k: v for k, v in self.ppr(dd.find(W + "pPrDefault/" + W + "pPr")).items()
                                 if not k.startswith("_")}
        for st in root.findall(W + "style"):
            kind = st.get(W + "type", "paragraph")
            if kind not in ("paragraph", "character", "table"):
                continue
            sid = st.get(W + "styleId")
            name = wv(st.find(W + "name"), sid)
            pp = self.ppr(st.find(W + "pPr"))
            numid = pp.pop("_numid", None)
            s = d.add_style(sid, _display(name), kind, based=wv(st.find(W + "basedOn")),
                            nxt=wv(st.find(W + "next")),
                            ppr={k: v for k, v in pp.items() if not k.startswith("_")},
                            rpr={k: v for k, v in self.rpr(st.find(W + "rPr")).items() if not k.startswith("_")},
                            default=st.get(W + "default") in ("1", "true"))
            if numid:
                s["_numid"] = numid
        if not d.style("Normal"):
            d.add_style("Normal", "Normal", default=not any(s.get("default") and s["type"] == "paragraph" for s in d.styles))

    def default_para(self):
        for s in self.doc.styles:
            if s.get("default") and s["type"] == "paragraph":
                return s["id"]
        return "Normal"

    def read_numbering(self):
        root = self.xml("word/numbering.xml")
        self.numid_map = {}
        if root is None:
            return
        abstract = {}
        for an in root.findall(W + "abstractNum"):
            levels = []
            byl = {}
            for lv in an.findall(W + "lvl"):
                i = num(lv.get(W + "ilvl"), 0)
                ind = lv.find(W + "pPr/" + W + "ind")
                l = {"start": num(wv(lv.find(W + "start")), 1), "fmt": wv(lv.find(W + "numFmt"), "decimal"),
                     "text": wv(lv.find(W + "lvlText"), ""), "jc": wv(lv.find(W + "lvlJc"), "left"),
                     "ind": num(ind.get(W + "left") or ind.get(W + "start"), 720 * (i + 1)) if ind is not None else 720 * (i + 1),
                     "hang": num(ind.get(W + "hanging"), 360) if ind is not None else 360}
                rp = self.rpr(lv.find(W + "rPr"))
                if rp.get("font"):
                    l["font"] = rp["font"]
                byl[i] = l
            for i in range(9):
                levels.append(byl.get(i, {"fmt": "decimal", "text": "%%%d." % (i + 1), "ind": 720 * (i + 1), "hang": 360}))
            self.doc.lists.append(levels)
            abstract[an.get(W + "abstractNumId")] = len(self.doc.lists) - 1
        for n in root.findall(W + "num"):
            aid = wv(n.find(W + "abstractNumId"))
            if aid not in abstract:
                continue
            idx = abstract[aid]
            restart = False
            ovs = n.findall(W + "lvlOverride")
            if ovs:
                levels = [dict(l) for l in self.doc.lists[idx]]
                for ov in ovs:
                    i = num(ov.get(W + "ilvl"), 0)
                    so = ov.find(W + "startOverride")
                    if so is not None and i < 9:
                        levels[i]["start"] = num(wv(so), 1)
                        restart = True
                    lvl = ov.find(W + "lvl")
                    if lvl is not None and i < 9:
                        levels[i]["fmt"] = wv(lvl.find(W + "numFmt"), levels[i]["fmt"])
                        levels[i]["text"] = wv(lvl.find(W + "lvlText"), levels[i]["text"])
                if levels != self.doc.lists[idx]:
                    self.doc.lists.append(levels)
                    idx = len(self.doc.lists) - 1
            self.doc.nums.append((idx, restart))
            self.numid_map[num(n.get(W + "numId"))] = len(self.doc.nums) - 1

    # -------------------------------------------------------------- content
    def read(self):
        self.read_theme()
        self.read_styles()
        self.read_numbering()
        self.read_meta()
        st = self.xml("word/settings.xml")
        if st is not None:
            ts = st.find(W + "defaultTabStop")
            if ts is not None:
                self.doc.tab_stop = num(wv(ts), 720)
        self.read_comments()
        self.notes = {}
        for kind in ("footnotes", "endnotes"):
            root = self.xml("word/%s.xml" % kind)
            rels = self.rels("word/%s.xml" % kind)
            if root is None:
                continue
            for n in root:
                if n.get(W + "type") in ("separator", "continuationSeparator", "continuationNotice"):
                    continue
                self.notes[(kind, n.get(W + "id"))] = (n, rels)
        body = self.xml("word/document.xml").find(W + "body")
        self.part_rels = self.rels("word/document.xml")
        sec = B.section()
        self.doc.sections.append(sec)
        self.cur = sec
        self.fstack = []
        self.blocks(body, sec["blocks"], top=True)
        final = body.find(W + "sectPr")
        if final is not None:
            self.apply_sect(sec, final)
        return self.doc

    def read_meta(self):
        root = self.xml("docProps/core.xml")
        if root is None:
            return
        for el in root:
            tag = el.tag.split("}")[-1]
            if tag in ("title", "subject", "creator", "keywords", "description") and el.text:
                self.doc.meta[tag] = el.text
            elif tag in ("created", "modified") and el.text:
                self.doc.meta[tag] = el.text

    def read_comments(self):
        root = self.xml("word/comments.xml")
        if root is None:
            return
        rels = self.rels("word/comments.xml")
        for c in root.findall(W + "comment"):
            cid = len(self.doc.comments)
            self.comment_map[c.get(W + "id")] = cid
            saved = getattr(self, "part_rels", None)
            self.part_rels = rels
            blocks = []
            self.fstack = []
            self.blocks(c, blocks)
            self.part_rels = saved
            for b in blocks:
                if not b.get("table"):
                    b["runs"] = [r for r in b["runs"] if r.get("t") != "_annref"]
            self.doc.comments.append({"id": cid, "author": c.get(W + "author", ""),
                                      "initials": c.get(W + "initials", ""),
                                      "date": c.get(W + "date", ""), "blocks": blocks})

    def apply_sect(self, sec, sp):
        pg = sp.find(W + "pgSz")
        if pg is not None:
            sec["w"] = num(pg.get(W + "w"), 12240)
            sec["h"] = num(pg.get(W + "h"), 15840)
            sec["landscape"] = pg.get(W + "orient") == "landscape"
        mg = sp.find(W + "pgMar")
        if mg is not None:
            for k in ("top", "right", "bottom", "left", "header", "footer", "gutter"):
                if mg.get(W + k) is not None:
                    sec["margins"][k] = abs(num(mg.get(W + k)))
        cols = sp.find(W + "cols")
        if cols is not None and num(cols.get(W + "num"), 1) > 1:
            sec["cols"] = num(cols.get(W + "num"))
            sec["col_space"] = num(cols.get(W + "space"), 720)
        t = sp.find(W + "type")
        if t is not None:
            sec["break"] = wv(t, "nextPage")
        sec["title_pg"] = on(sp.find(W + "titlePg")) or False
        pn = sp.find(W + "pgNumType")
        if pn is not None and pn.get(W + "start"):
            sec["page_start"] = num(pn.get(W + "start"))
        for kind, store in (("header", sec["headers"]), ("footer", sec["footers"])):
            for ref in sp.findall(W + kind + "Reference"):
                rid = ref.get(R + "id")
                rel = self.part_rels.get(rid)
                if not rel:
                    continue
                root = self.xml(rel[1])
                if root is None:
                    continue
                saved = self.part_rels
                self.part_rels = self.rels(rel[1])
                blocks = []
                self.blocks(root, blocks)
                self.part_rels = saved
                store[ref.get(W + "type", "default")] = blocks

    def blocks(self, parent, out, top=False):
        for el in parent:
            tag = el.tag
            if tag == W + "p":
                p = self.paragraph(el)
                out.append(p)
                sp = p["ppr"].pop("_sect", None)
                if sp is not None and top:
                    self.apply_sect(self.cur, sp)
                    nxt = B.section()
                    self.doc.sections.append(nxt)
                    self.cur = nxt
                    out = nxt["blocks"]
            elif tag == W + "tbl":
                out.append(self.table(el))
            elif tag == W + "sdt":
                c = el.find(W + "sdtContent")
                if c is not None:
                    self.blocks(c, out, top)
                    if top:
                        out = self.cur["blocks"]
            elif tag in (W + "customXml", W + "ins", W + "moveTo"):
                self.blocks(el, out, top)
                if top:
                    out = self.cur["blocks"]
            elif tag == MC + "AlternateContent":
                ch = el.find(MC + "Choice")
                if ch is None:
                    ch = el.find(MC + "Fallback")
                if ch is not None:
                    self.blocks(ch, out, top)

    def paragraph(self, el):
        pp = self.ppr(el.find(W + "pPr"))
        dflt = getattr(self, "_dflt", None) or self.__dict__.setdefault("_dflt", self.default_para())
        sid = pp.pop("_style", None) or dflt
        if not self.doc.style(sid):
            sid = dflt
        mark = pp.pop("_mark", {})
        mark.pop("_cstyle", None)
        numid = pp.pop("_numid", None)
        if numid is None:
            st = self.doc.style(sid)
            numid = st.get("_numid") if st else None
        if numid is not None:
            nid, lvl = numid
            if nid and nid in getattr(self, "numid_map", {}):
                pp["num"] = (self.numid_map[nid], min(8, lvl))
            elif nid == 0 and "num" in pp:
                pp.pop("num")
        p = {"style": sid, "ppr": pp, "rpr": mark, "runs": []}
        self.inline(el, p["runs"])
        # a field running on into the next paragraphs (a table of contents)
        if self.fstack and self.fstack[0]["state"] in ("result", "code") and len(self.fstack) == 1:
            f = self.fstack[0]
            p["runs"].append({"t": "fbegin", "instr": f["instr"].strip()})
            p["runs"].append({"t": "fsep"})
            p["runs"].extend(f["result"])
            f["result"] = []
            f["state"] = "pass"
            f["split"] = True
        return p

    def inline(self, parent, runs, rpr_base=None):
        for el in parent:
            tag = el.tag
            if tag == W + "r":
                self.run(el, runs)
            elif tag == W + "hyperlink":
                inner = []
                self.inline(el, inner)
                rid = el.get(R + "id")
                anchor = el.get(W + "anchor")
                url = None
                if rid and rid in self.part_rels:
                    url = self.part_rels[rid][1]
                runs.append({"t": "link", "url": url, "anchor": anchor if not url else None, "runs": inner})
            elif tag == W + "fldSimple":
                inner = []
                self.inline(el, inner)
                runs.append({"t": "field", "instr": el.get(W + "instr", "").strip(), "result": inner})
            elif tag in (W + "smartTag", W + "customXml", W + "ins", W + "moveTo", W + "dir", W + "bdo"):
                self.inline(el, runs)
            elif tag == W + "sdt":
                c = el.find(W + "sdtContent")
                if c is not None:
                    self.inline(c, runs)
            elif tag == W + "bookmarkStart":
                n = el.get(W + "name", "")
                if n and not n.startswith("_GoBack"):
                    self.__dict__.setdefault("bm", {})[el.get(W + "id")] = n
                    runs.append({"t": "bmstart", "name": n})
            elif tag == W + "bookmarkEnd":
                n = getattr(self, "bm", {}).get(el.get(W + "id"))
                if n:
                    runs.append({"t": "bmend", "name": n})
            elif tag == W + "commentRangeStart":
                cid = self.comment_map.get(el.get(W + "id"))
                if cid is not None:
                    runs.append({"t": "cstart", "id": cid})
            elif tag == W + "commentRangeEnd":
                cid = self.comment_map.get(el.get(W + "id"))
                if cid is not None:
                    runs.append({"t": "cend", "id": cid})
            elif tag == MC + "AlternateContent":
                ch = el.find(MC + "Choice")
                if ch is None:
                    ch = el.find(MC + "Fallback")
                if ch is not None:
                    self.inline(ch, runs)

    def emit(self, runs, r):
        """Runs inside a field's result go to the field; inside its code, nowhere."""
        if self.fstack and self.fstack[-1]["state"] != "pass":
            f = self.fstack[-1]
            if f["state"] == "code":
                if r.get("t") == "text":
                    f["instr"] += r["text"]
                return
            if len(self.fstack) > 1:
                # nested fields: the outer result shows the inner results' text
                pass
            f["result"].append(r)
            return
        runs.append(r)

    def run(self, el, runs):
        rp = self.rpr(el.find(W + "rPr"))
        cst = rp.pop("_cstyle", None)
        if cst and not self.doc.style(cst):
            cst = None
        for ch in el:
            tag = ch.tag
            if tag == W + "t":
                self.emit(runs, {"t": "text", "text": ch.text or "", "rpr": rp, "cstyle": cst})
            elif tag == W + "instrText":
                if self.fstack and self.fstack[-1]["state"] == "code":
                    self.fstack[-1]["instr"] += ch.text or ""
            elif tag == W + "delText":
                continue
            elif tag in (W + "tab", W + "ptab"):
                self.emit(runs, {"t": "tab", "rpr": rp})
            elif tag in (W + "br", W + "cr"):
                typ = ch.get(W + "type")
                self.emit(runs, {"t": {"page": "page", "column": "col"}.get(typ, "br"), "rpr": rp})
            elif tag == W + "noBreakHyphen":
                self.emit(runs, {"t": "text", "text": "‑", "rpr": rp, "cstyle": cst})
            elif tag == W + "softHyphen":
                self.emit(runs, {"t": "text", "text": "­", "rpr": rp, "cstyle": cst})
            elif tag == W + "sym":
                c = ch.get(W + "char", "")
                try:
                    code = int(c, 16)
                    if code >= 0xF000:
                        code -= 0xF000
                    r2 = dict(rp, font=ch.get(W + "font") or rp.get("font"))
                    self.emit(runs, {"t": "text", "text": chr(code), "rpr": r2, "cstyle": cst})
                except ValueError:
                    pass
            elif tag == W + "fldChar":
                typ = ch.get(W + "fldCharType")
                if typ == "begin":
                    self.fstack.append({"state": "code", "instr": "", "result": [], "rpr": rp,
                                        "runs": runs, "split": False})
                elif typ == "separate" and self.fstack and self.fstack[-1]["state"] == "code":
                    self.fstack[-1]["state"] = "result"
                elif typ == "end" and self.fstack:
                    f = self.fstack.pop()
                    fr = {"t": "field", "instr": f["instr"].strip(), "result": f["result"], "rpr": f["rpr"]}
                    if f.get("split"):
                        # the field began in an earlier paragraph
                        runs.append({"t": "fend"})
                    elif self.fstack:
                        self.fstack[-1]["result"].extend(f["result"])
                    else:
                        runs.append(fr)
            elif tag == W + "drawing":
                img = self.drawing(ch)
                if img:
                    self.emit(runs, img)
            elif tag == W + "pict" or tag == W + "object":
                img = self.vml(ch)
                if img:
                    self.emit(runs, img)
            elif tag in (W + "footnoteReference", W + "endnoteReference"):
                kind = "footnotes" if tag == W + "footnoteReference" else "endnotes"
                n = self.notes.get((kind, ch.get(W + "id")))
                blocks = []
                if n is not None:
                    saved = self.part_rels
                    self.part_rels = n[1]
                    fs = self.fstack
                    self.fstack = []
                    self.blocks(n[0], blocks)
                    self.fstack = fs
                    self.part_rels = saved
                    if blocks and not blocks[0].get("table"):
                        rs = blocks[0]["runs"]
                        # the note's own number mark and the space after it
                        while rs and rs[0].get("t") in ("_ref",):
                            rs.pop(0)
                        if rs and rs[0].get("t") == "text" and rs[0]["text"].startswith(" "):
                            rs[0]["text"] = rs[0]["text"][1:]
                self.emit(runs, {"t": "note", "kind": "endnote" if kind == "endnotes" else "footnote",
                                 "blocks": blocks, "rpr": {}})
            elif tag in (W + "footnoteRef", W + "endnoteRef"):
                runs.append({"t": "_ref"})
            elif tag == W + "annotationRef":
                runs.append({"t": "_annref"})
            elif tag == MC + "AlternateContent":
                c = ch.find(MC + "Choice")
                if c is None:
                    c = ch.find(MC + "Fallback")
                if c is not None:
                    for d in c:
                        if d.tag == W + "drawing":
                            img = self.drawing(d)
                            if img:
                                self.emit(runs, img)

    def image_data(self, rid):
        rel = self.part_rels.get(rid)
        if not rel or rel[2]:
            return None, None
        try:
            data = self.z.read(rel[1])
        except KeyError:
            return None, None
        ext = posixpath.splitext(rel[1])[1].lower().lstrip(".")
        return data, ext

    def drawing(self, el):
        box = el.find(WP + "inline")
        anchor = None
        if box is None:
            box = el.find(WP + "anchor")
            anchor = box
        if box is None:
            return None
        ext = box.find(WP + "extent")
        cx = num(ext.get("cx"), 914400) if ext is not None else 914400
        cy = num(ext.get("cy"), 914400) if ext is not None else 914400
        blip = box.find(".//" + A_ + "blip")
        if blip is None:
            return None
        data, fext = self.image_data(blip.get(R + "embed"))
        if not data:
            return None
        dp = box.find(WP + "docPr")
        r = {"t": "image", "data": data, "ext": fext or "png", "cx": cx, "cy": cy,
             "name": dp.get("name", "") if dp is not None else "", "descr": dp.get("descr", "") if dp is not None else ""}
        if anchor is not None:
            a = {"wrap": "square", "behind": anchor.get("behindDoc") in ("1", "true")}
            for w, k in (("wrapNone", "none"), ("wrapTopAndBottom", "top"), ("wrapSquare", "square"),
                         ("wrapTight", "tight"), ("wrapThrough", "tight")):
                if anchor.find(WP + w) is not None:
                    a["wrap"] = k
            for axis, key in (("positionH", "h"), ("positionV", "v")):
                pe = anchor.find(WP + axis)
                if pe is None:
                    continue
                a[key + "rel"] = pe.get("relativeFrom", "column")
                al = pe.find(WP + "align")
                off = pe.find(WP + "posOffset")
                if al is not None:
                    a[key + "align"] = al.text
                if off is not None:
                    a["x" if key == "h" else "y"] = num(off.text)
            r["anchor"] = a
        return r

    def vml(self, el):
        im = el.find(".//{urn:schemas-microsoft-com:vml}imagedata")
        if im is None:
            return None
        data, fext = self.image_data(im.get(R + "id"))
        if not data:
            return None
        shape = el.find(".//{urn:schemas-microsoft-com:vml}shape")
        w = h = 1440
        if shape is not None:
            for part in (shape.get("style") or "").split(";"):
                k, _, v = part.partition(":")
                v = v.strip()
                if k.strip() in ("width", "height"):
                    t = _css_twips(v)
                    if k.strip() == "width":
                        w = t
                    else:
                        h = t
        return {"t": "image", "data": data, "ext": fext or "png", "cx": w * B.EMU_PER_TWIP,
                "cy": h * B.EMU_PER_TWIP}

    def table(self, el):
        t = {"table": True, "rows": [], "cols": [], "borders": False}
        tp = el.find(W + "tblPr")
        tstyle = None
        if tp is not None:
            tstyle = wv(tp.find(W + "tblStyle"))
            jc = wv(tp.find(W + "jc"))
            if jc in ("center", "right", "end"):
                t["align"] = "right" if jc == "end" else jc
            ind = tp.find(W + "tblInd")
            if ind is not None:
                t["indent"] = num(ind.get(W + "w"))
            tb = tp.find(W + "tblBorders")
            if tb is not None:
                t["tborders"] = self.borders(tb)
        if tstyle and not t.get("tborders"):
            st = self.style_borders(tstyle)
            if st:
                t["tborders"] = st
        t["style"] = tstyle if tstyle and self.doc.style(tstyle) else None
        grid = el.find(W + "tblGrid")
        if grid is not None:
            t["cols"] = [num(g.get(W + "w"), 1440) for g in grid.findall(W + "gridCol")]
        for tr in el.findall(W + "tr"):
            row = {"cells": []}
            trp = tr.find(W + "trPr")
            if trp is not None:
                row["header"] = on(trp.find(W + "tblHeader")) or False
                h = trp.find(W + "trHeight")
                if h is not None:
                    row["height"] = num(wv(h))
                    row["exact"] = h.get(W + "hRule") == "exact"
                row["cant_split"] = on(trp.find(W + "cantSplit")) or False
            for tc in tr.findall(W + "tc"):
                c = {"span": 1, "blocks": []}
                pr = tc.find(W + "tcPr")
                if pr is not None:
                    gs = pr.find(W + "gridSpan")
                    if gs is not None:
                        c["span"] = max(1, num(wv(gs), 1))
                    vm = pr.find(W + "vMerge")
                    if vm is not None:
                        c["vmerge"] = "restart" if wv(vm) == "restart" else "cont"
                    sh = pr.find(W + "shd")
                    if sh is not None and sh.get(W + "fill") not in (None, "auto"):
                        c["shd"] = sh.get(W + "fill").upper()
                    bd = pr.find(W + "tcBorders")
                    if bd is not None:
                        c["borders"] = self.borders(bd)
                    va = wv(pr.find(W + "vAlign"))
                    if va in ("center", "bottom"):
                        c["valign"] = va
                    w = pr.find(W + "tcW")
                    if w is not None and w.get(W + "type") in ("dxa", None):
                        c["width"] = num(w.get(W + "w"))
                self.blocks(tc, c["blocks"])
                row["cells"].append(c)
            t["rows"].append(row)
        if tstyle:
            self.apply_table_style(t, tstyle, tp)
        return t

    def table_style_parts(self, sid, depth=0):
        """{condition: (cell shading, run props, borders)} of a table style and those it is based on."""
        root = getattr(self, "_styles_root", None)
        if root is None:
            root = self._styles_root = self.xml("word/styles.xml")
        if root is None or depth > 5:
            return {}
        for st in root.findall(W + "style"):
            if st.get(W + "styleId") != sid:
                continue
            based = wv(st.find(W + "basedOn"))
            out = self.table_style_parts(based, depth + 1) if based else {}
            whole = (self._shd(st.find(W + "tcPr")), self.rpr(st.find(W + "rPr")))
            if whole[0] or whole[1]:
                out["wholeTable"] = whole
            pp = {k: v for k, v in self.ppr(st.find(W + "pPr")).items() if not k.startswith("_")}
            if pp:
                out["_ppr"] = dict(out.get("_ppr") or {}, **pp)
            for c in st.findall(W + "tblStylePr"):
                out[c.get(W + "type")] = (self._shd(c.find(W + "tcPr")), self.rpr(c.find(W + "rPr")))
            return out
        return {}

    def _shd(self, tcpr):
        if tcpr is None:
            return None
        sh = tcpr.find(W + "shd")
        if sh is not None and sh.get(W + "fill") not in (None, "auto"):
            return sh.get(W + "fill").upper()
        return None

    def apply_table_style(self, t, sid, tp):
        parts = self.table_style_parts(sid)
        if not parts:
            return
        tppr = parts.pop("_ppr", None)
        if tppr:
            dflt = self.default_para()
            for row in t["rows"]:
                for c in row["cells"]:
                    for b in B.walk_blocks(c["blocks"]):
                        if b.get("style") == dflt:
                            for k, v in tppr.items():
                                b["ppr"].setdefault(k, v)
        look = {"firstRow": True, "lastRow": False, "firstColumn": True, "lastColumn": False,
                "noHBand": False, "noVBand": True}
        lk = tp.find(W + "tblLook") if tp is not None else None
        if lk is not None:
            v = lk.get(W + "val")
            if v:
                n = int(v, 16)
                look = {"firstRow": bool(n & 0x20), "lastRow": bool(n & 0x40), "firstColumn": bool(n & 0x80),
                        "lastColumn": bool(n & 0x100), "noHBand": bool(n & 0x200), "noVBand": bool(n & 0x400)}
            for k in look:
                if lk.get(W + k) is not None:
                    look[k] = lk.get(W + k) in ("1", "true")
        nrows = len(t["rows"])
        band = 0
        for ri, row in enumerate(t["rows"]):
            first = look["firstRow"] and ri == 0
            last = look["lastRow"] and ri == nrows - 1 and nrows > 1
            if not first and not last:
                band += 1
            ncell = len(row["cells"])
            for ci, c in enumerate(row["cells"]):
                conds = ["wholeTable"]
                if not look["noHBand"] and not first and not last:
                    conds.append("band1Horz" if band % 2 == 1 else "band2Horz")
                if not look["noVBand"]:
                    conds.append("band1Vert" if ci % 2 == 0 else "band2Vert")
                if look["firstColumn"] and ci == 0:
                    conds.append("firstCol")
                if look["lastColumn"] and ci == ncell - 1:
                    conds.append("lastCol")
                if first:
                    conds.append("firstRow")
                if last:
                    conds.append("lastRow")
                shd = None
                rp = {}
                for cond in conds:
                    if cond in parts:
                        sh, r = parts[cond]
                        if sh:
                            shd = sh
                        rp.update({k: v for k, v in r.items() if not k.startswith("_")})
                if shd and not c.get("shd"):
                    c["shd"] = shd
                if rp:
                    for b in B.walk_blocks(c["blocks"]):
                        for r in b.get("runs", []):
                            if r.get("t") == "text":
                                merged = dict(rp)
                                merged.update(r.get("rpr") or {})
                                r["rpr"] = merged

    def borders(self, el):
        b = {}
        for side in el:
            s = side.tag[len(W):]
            s = {"start": "left", "end": "right"}.get(s, s)
            if wv(side) in ("nil", "none", None):
                b[s] = None
                continue
            b[s] = (num(side.get(W + "sz"), 4), (side.get(W + "color") or "000000").replace("auto", "000000"),
                    wv(side), num(side.get(W + "space"), 0))
        return b

    def style_borders(self, sid, depth=0):
        root = getattr(self, "_styles_root", None)
        if root is None:
            root = self._styles_root = self.xml("word/styles.xml")
        if root is None or depth > 5:
            return None
        for st in root.findall(W + "style"):
            if st.get(W + "styleId") == sid:
                tb = st.find(W + "tblPr/" + W + "tblBorders")
                if tb is not None:
                    return self.borders(tb)
                based = wv(st.find(W + "basedOn"))
                return self.style_borders(based, depth + 1) if based else None
        return None


def _css_twips(v):
    v = v.strip()
    for unit, f in (("pt", 20.0), ("in", 1440.0), ("cm", 566.929), ("mm", 56.6929), ("px", 15.0)):
        if v.endswith(unit):
            try:
                return int(float(v[:-len(unit)]) * f)
            except ValueError:
                return 1440
    try:
        return int(float(v) * 15)
    except ValueError:
        return 1440


def _display(name):
    """Word stores some built-in names in lower case."""
    low = {v.lower(): k for k, v in B.BUILTIN.items()}
    for k in B.BUILTIN:
        if k.lower() == (name or "").lower():
            return k
    return name


def read(path):
    return Reader(path).read()
