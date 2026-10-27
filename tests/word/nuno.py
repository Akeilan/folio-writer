# The document interface the Word-parity scenarios read (getText, cursors,
# paragraphs, tables, search, undo titles...), answered by Folio's own engine,
# so the same scenarios check the new engine. Test-only: the app itself
# talks to the engine directly.
from folio.native.uno_props import CursorProps


class _Coll:
    def __init__(self, items, names=None):
        self.items = list(items)
        self.names = names or ["Item%d" % (i + 1) for i in range(len(self.items))]

    def getCount(self):
        return len(self.items)

    def getByIndex(self, i):
        return self.items[i]

    def getElementNames(self):
        return tuple(self.names)

    def getByName(self, n):
        return self.items[self.names.index(n)]

    def hasByName(self, n):
        return n in self.names

    def hasElements(self):
        return bool(self.items)

    def createEnumeration(self):
        return _Enum(self.items)


class _Enum:
    def __init__(self, items):
        self.items = list(items)

    def hasMoreElements(self):
        return bool(self.items)

    def nextElement(self):
        return self.items.pop(0)


def _paras(ed):
    """Body paragraphs in order (tables as their cells' paragraphs)."""
    out = []
    for kind, node, ti in ed.body_blocks():
        if kind == "p":
            out.append(node)
        else:
            for row in ed.table_cells(ti):
                for cell in row:
                    out.extend(cell)
    return out


def _top_paras(ed):
    return [n for k, n, _t in ed.body_blocks() if k == "p"]


def _ptext(ed, p):
    return ed.para_text_of(p).replace("￼", "")


class _Range:
    """A stretch of the body: (para, offset) to (para, offset)."""

    def __init__(self, m, a, b=None):
        object.__setattr__(self, "m", m)
        object.__setattr__(self, "a", tuple(a))
        object.__setattr__(self, "b", tuple(b if b is not None else a))

    @property
    def ed(self):
        return self.m.ed

    # ------------------------------------------------------------ text
    def _ordered(self):
        order = {p: i for i, p in enumerate(_paras(self.ed))}
        ka = (order.get(self.a[0], 0), self.a[1])
        kb = (order.get(self.b[0], 0), self.b[1])
        return (self.a, self.b) if ka <= kb else (self.b, self.a)

    def getString(self):
        (pa, oa), (pb, ob) = self._ordered()
        paras = _paras(self.ed)
        if pa not in paras or pb not in paras:
            return ""
        i, j = paras.index(pa), paras.index(pb)
        if i == j:
            return _ptext(self.ed, pa)[oa:ob]
        parts = [_ptext(self.ed, pa)[oa:]]
        for p in paras[i + 1:j]:
            parts.append(_ptext(self.ed, p))
        parts.append(_ptext(self.ed, pb)[:ob])
        return "\n".join(parts)

    def _select(self):
        (pa, oa), (pb, ob) = self._ordered()
        return self.ed.select_nodes(pa, oa, pb, ob)

    def _with_selection(self, fn):
        ed = self.ed
        keep = (ed.anchor_pos(), ed.caret_pos())
        self._select()
        try:
            return fn()
        finally:
            ed.select_nodes(keep[0][0], keep[0][1], keep[1][0], keep[1][1])

    def setString(self, s):
        ed = self.ed

        def go():
            if ed.has_selection():
                if s:
                    ed.type_text(s)
                else:
                    ed.delete(True, False)
            elif s:
                ed.type_text(s)
        (pa, oa), _b = self._ordered()
        self._select()
        go()
        self.m.changed()
        object.__setattr__(self, "a", (pa, oa))
        object.__setattr__(self, "b", tuple(ed.caret_pos()))

    def getStart(self):
        a, _b = self._ordered()
        return _Range(self.m, a)

    def getEnd(self):
        _a, b = self._ordered()
        return _Range(self.m, b)

    def getText(self):
        return self.m.getText()

    # ------------------------------------------------------------ formatting
    def __getattr__(self, k):
        if k in EXTRA_PROPS:
            return self._with_selection(lambda: EXTRA_PROPS[k](self.m, self))
        if k[:1].isupper():
            return self._with_selection(lambda: getattr(CursorProps(self.m.eng), k))
        raise AttributeError(k)

    def __setattr__(self, k, v):
        if k[:1].isupper():
            def go():
                setattr(CursorProps(self.m.eng), k, v)
            self._with_selection(go)
            self.m.changed()
            return
        object.__setattr__(self, k, v)

    def getPropertyValue(self, k):
        return getattr(self, k)

    def setPropertyValue(self, k, v):
        setattr(self, k, v)

    def setPropertyToDefault(self, k):
        pass

    def setPropertiesToDefault(self, ks):
        pass

    def supportsService(self, name):
        return name in ("com.sun.star.text.Paragraph", "com.sun.star.text.TextRange")


def _link(m, r):
    ed = m.ed
    (pa, oa), (pb, ob) = r._ordered()
    mid = (oa + ob) // 2 if pa == pb else oa + 1
    ed.select_nodes(pa, mid, pa, mid)
    return ed.link_at_caret() or ""


def _border(side):
    def get(m, r):
        b = m.ed.para_values().get("borders", {}).get(side)

        class Line:
            pass
        ln = Line()
        w = int(round(b[1] / 8.0 * 2540 / 72)) if b else 0
        ln.OuterLineWidth = ln.LineWidth = w
        ln.InnerLineWidth = 0
        ln.LineDistance = 0
        ln.Color = (b[3] if b[3] >= 0 else 0) if b else 0
        ln.LineStyle = 0 if b else None
        return ln
    return get


def _table_of(m, para):
    """(table, cell) holding para, or (None, None)."""
    ed = m.ed
    for k, node, ti in ed.body_blocks():
        if k != "t":
            continue
        t = _Table(m, ti, node)
        for r, row in enumerate(t.cells):
            for c, paras in enumerate(row):
                if para in paras:
                    cell = _Cell(m, paras)
                    cell.CellName = _Table._name(r, c)
                    return t, cell
    return None, None


def _li(m, r):
    try:
        return m.ed.list_info_of(r._ordered()[0][0])
    except Exception:
        return m.ed.list_info()


EXTRA_PROPS = {
    "PageStyleName": lambda m, r: "Standard",
    "PageDescName": lambda m, r: None,
    "TextTable": lambda m, r: _table_of(m, r._ordered()[0][0])[0],
    "Cell": lambda m, r: _table_of(m, r._ordered()[0][0])[1],
    "TopBorder": _border("top"), "BottomBorder": _border("bottom"),
    "LeftBorder": _border("left"), "RightBorder": _border("right"),
    "NumberingIsNumber": lambda m, r: _li(m, r) is not None,
    "NumberingLevel": lambda m, r: (_li(m, r) or (0, 0))[1],
    "ListLabelString": lambda m, r: (_li(m, r) or (0, 0, 0, ""))[3],
    "NumberingRules": lambda m, r: _li(m, r),
    "HyperLinkURL": _link,
}


class _Cursor(_Range):
    """A text cursor: a range that moves."""

    def _move(self, pos, expand):
        if expand:
            object.__setattr__(self, "b", tuple(pos))
        else:
            object.__setattr__(self, "a", tuple(pos))
            object.__setattr__(self, "b", tuple(pos))
        return True

    def gotoStart(self, expand):
        paras = _paras(self.ed)
        return self._move((paras[0], 0), expand) if paras else False

    def gotoEnd(self, expand):
        paras = _paras(self.ed)
        if not paras:
            return False
        p = paras[-1] if not _top_paras(self.ed) else _top_paras(self.ed)[-1]
        return self._move((p, len(_ptext(self.ed, p))), expand)

    def gotoRange(self, r, expand):
        if expand:
            object.__setattr__(self, "b", tuple(r.b))
        else:
            object.__setattr__(self, "a", tuple(r.a))
            object.__setattr__(self, "b", tuple(r.b))
        return True

    def gotoStartOfParagraph(self, expand):
        return self._move((self.b[0], 0), expand)

    def gotoEndOfParagraph(self, expand):
        return self._move((self.b[0], len(_ptext(self.ed, self.b[0]))), expand)

    def gotoNextParagraph(self, expand):
        paras = _paras(self.ed)
        i = paras.index(self.b[0]) if self.b[0] in paras else -1
        if i < 0 or i + 1 >= len(paras):
            return False
        return self._move((paras[i + 1], 0), expand)

    def gotoPreviousParagraph(self, expand):
        paras = _paras(self.ed)
        i = paras.index(self.b[0]) if self.b[0] in paras else -1
        if i <= 0:
            return False
        return self._move((paras[i - 1], 0), expand)

    def goRight(self, n, expand):
        p, o = self.b
        paras = _paras(self.ed)
        for _ in range(n):
            if o < len(_ptext(self.ed, p)):
                o += 1
            else:
                i = paras.index(p)
                if i + 1 >= len(paras):
                    return False
                p, o = paras[i + 1], 0
        return self._move((p, o), expand)

    def goLeft(self, n, expand):
        p, o = self.b
        paras = _paras(self.ed)
        for _ in range(n):
            if o > 0:
                o -= 1
            else:
                i = paras.index(p)
                if i == 0:
                    return False
                p = paras[i - 1]
                o = len(_ptext(self.ed, p))
        return self._move((p, o), expand)

    def collapseToStart(self):
        a, _b = self._ordered()
        object.__setattr__(self, "a", a)
        object.__setattr__(self, "b", a)

    def collapseToEnd(self):
        _a, b = self._ordered()
        object.__setattr__(self, "a", b)
        object.__setattr__(self, "b", b)

    def isCollapsed(self):
        return self.a == self.b

    def isStartOfParagraph(self):
        return self.b[1] == 0

    def isEndOfParagraph(self):
        return self.b[1] == len(_ptext(self.ed, self.b[0]))


class _ViewCursor(_Cursor):
    """The caret and selection."""

    def __init__(self, m):
        object.__setattr__(self, "m", m)

    @property
    def a(self):
        return tuple(self.m.ed.anchor_pos())

    @property
    def b(self):
        return tuple(self.m.ed.caret_pos())

    def _move(self, pos, expand):
        ed = self.m.ed
        a = self.a if expand else tuple(pos)
        ed.select_nodes(a[0], a[1], pos[0], pos[1])
        self.m.eng.view.after_move()
        return True

    def gotoRange(self, r, expand):
        return self._move(r.a, expand)

    def collapseToStart(self):
        a, _b = self._ordered()
        self._move(a, False)

    def collapseToEnd(self):
        _a, b = self._ordered()
        self._move(b, False)

    def setString(self, s):
        ed = self.m.ed
        if ed.has_selection():
            if s:
                ed.type_text(s)
            else:
                ed.delete(True, False)
        elif s:
            ed.type_text(s)
        self.m.changed()

    def getPage(self):
        return self.m.ed.caret_page() + 1

    def jumpToFirstPage(self):
        return self.gotoStart(False)

    def jumpToLastPage(self):
        return self.gotoEnd(False)

    def getPosition(self):
        r = self.m.ed.caret_rect()

        class P:
            pass
        p = P()
        p.X = int((r[1] if r else 0) * 2540 / 72)
        p.Y = int((r[2] if r else 0) * 2540 / 72)
        return p

    def __setattr__(self, k, v):
        if k[:1].isupper():
            setattr(CursorProps(self.m.eng), k, v)
            self.m.changed()
            return
        object.__setattr__(self, k, v)

    def __getattr__(self, k):
        if k in EXTRA_PROPS:
            return EXTRA_PROPS[k](self.m, _Range(self.m, self.a, self.b))
        if k[:1].isupper():
            return getattr(CursorProps(self.m.eng), k)
        raise AttributeError(k)


class _Para(_Range):
    def __init__(self, m, p):
        _Range.__init__(self, m, (p, 0), (p, len(_ptext(m.ed, p))))

    def createEnumeration(self):
        return _Enum([self])

    def getImplementationName(self):
        return "SwXParagraph"


class _Cell:
    def __init__(self, m, paras):
        self.m, self.paras = m, paras

    def getString(self):
        return "\n".join(_ptext(self.m.ed, p) for p in self.paras)

    def setString(self, s):
        if self.paras:
            _Range(self.m, (self.paras[0], 0), (self.paras[-1], len(_ptext(self.m.ed, self.paras[-1])))).setString(s)

    def getText(self):
        m = self.m
        cell = self

        class T:
            def getString(self):
                return cell.getString()

            def createTextCursor(self):
                return _Cursor(m, (cell.paras[0], 0))

            def createTextCursorByRange(self, r):
                a, b = r._ordered()
                return _Cursor(m, a, b)

            def getStart(self):
                return _Range(m, (cell.paras[0], 0))

            def getEnd(self):
                p = cell.paras[-1]
                return _Range(m, (p, len(_ptext(m.ed, p))))

            def getText(self):
                return self

            def createEnumeration(self):
                return _Enum([_Para(m, p) for p in cell.paras])

            def compareRegionStarts(self, x, y):
                return m.getText().compareRegionStarts(x, y)
        return T()

    def getStart(self):
        return self.getText().getStart()

    def createTextCursor(self):
        return _Cursor(self.m, (self.paras[0], 0))


class _Table:
    def __init__(self, m, index, node):
        self.m, self.index, self.node = m, index, node

    @property
    def cells(self):
        return self.m.ed.table_cells(self.index)

    @staticmethod
    def _name(r, c):
        s = ""
        c += 1
        while c:
            c, k = divmod(c - 1, 26)
            s = chr(65 + k) + s
        return "%s%d" % (s, r + 1)

    def getCellNames(self):
        return tuple(self._name(r, c) for r, row in enumerate(self.cells) for c in range(len(row)))

    def getCellByName(self, n):
        for r, row in enumerate(self.cells):
            for c, paras in enumerate(row):
                if self._name(r, c) == n:
                    return _Cell(self.m, paras)
        return None

    def getCellRangeByName(self, n):
        t = self

        class R:
            def __init__(self):
                self.names = n

            def setPropertyValue(self, k, v):
                setattr(self, k, v)

            def getPropertyValue(self, k):
                return getattr(self, k, None)
        return R()

    def getCellByPosition(self, c, r):
        return _Cell(self.m, self.cells[r][c])

    def getRows(self):
        return _Coll(self.cells)

    def getColumns(self):
        return _Coll(range(max((len(r) for r in self.cells), default=0)))

    def getName(self):
        return "Table%d" % (self.index + 1)

    @property
    def Name(self):
        return self.getName()

    def dispose(self):
        pass

    def supportsService(self, name):
        return name == "com.sun.star.text.TextTable"

    def getAnchor(self):
        paras = self.cells[0][0] if self.cells and self.cells[0] else []
        return _Range(self.m, (paras[0], 0)) if paras else None


class _Text(_Range):
    def __init__(self, m):
        object.__setattr__(self, "m", m)

    @property
    def a(self):
        paras = _paras(self.m.ed)
        return (paras[0], 0) if paras else (0, 0)

    @property
    def b(self):
        tops = _top_paras(self.m.ed)
        p = tops[-1] if tops else self.a[0]
        return (p, len(_ptext(self.m.ed, p)))

    def getString(self):
        ed = self.m.ed
        return "\n".join(_ptext(ed, p) for p in _top_paras(ed))

    def setString(self, s):
        ed = self.m.ed
        ed.select_all()
        if s:
            ed.type_text(s)
        else:
            ed.delete(True, False)
        self.m.changed()

    def getStart(self):
        return _Range(self.m, self.a)

    def getEnd(self):
        return _Range(self.m, self.b)

    def createTextCursor(self):
        return _Cursor(self.m, self.a)

    def createTextCursorByRange(self, r):
        a, b = r._ordered() if hasattr(r, "_ordered") else (r.a, r.b)
        return _Cursor(self.m, a, b)

    def createEnumeration(self):
        ed = self.m.ed
        items = []
        for kind, node, ti in ed.body_blocks():
            items.append(_Para(self.m, node) if kind == "p" else _Table(self.m, ti, node))
        return _Enum(items)

    def insertString(self, r, s, absorb):
        if absorb and hasattr(r, "setString"):
            r.setString(s)
        else:
            _Range(self.m, r.b).setString(s)

    def insertControlCharacter(self, r, ch, absorb):
        _Range(self.m, r.b).setString("\n")

    def compareRegionStarts(self, x, y):
        order = {p: i for i, p in enumerate(_paras(self.m.ed))}
        kx = (order.get(x.a[0], 0), x.a[1])
        ky = (order.get(y.a[0], 0), y.a[1])
        return 1 if kx < ky else (-1 if kx > ky else 0)

    def getText(self):
        return self


MM = 2540.0 / 1440.0   # twips -> 1/100 mm


class _PageStyle:
    """A section's page, as the page style the tests read."""

    def __init__(self, m, sec=0):
        object.__setattr__(self, "m", m)
        object.__setattr__(self, "sec", sec)

    def _d(self):
        return self.m.ed.page_setup(self.sec) or {}

    def __getattr__(self, k):
        d = self._d()
        ed = self.m.ed
        pg = 0
        for i in range(ed.page_count()):
            if ed.page_section(i) == self.sec:
                pg = i
                break
        conv = {"Width": "width", "Height": "height", "TopMargin": "top", "BottomMargin": "bottom",
                "LeftMargin": "left", "RightMargin": "right"}
        if k in conv:
            return int(round((d.get(conv[k]) or 0) * MM))
        if k == "IsLandscape":
            return (d.get("width") or 0) > (d.get("height") or 0)
        if k == "HeaderIsOn":
            return bool(ed.page_hf(pg)[0])
        if k == "FooterIsOn":
            return bool(ed.page_hf(pg)[1])
        if k == "Name":
            return "Standard"
        if k == "TextColumns":
            class C:
                pass
            c = C()
            c.ColumnCount = d.get("cols") or 1
            c.getColumnCount = lambda: c.ColumnCount
            return c
        if k == "BackColor":
            return -1
        raise AttributeError(k)

    def getName(self):
        return "Standard"

    def getPropertyValue(self, k):
        return getattr(self, k)


class _PageStyles:
    def __init__(self, m):
        self.m = m

    def getByName(self, n):
        return _PageStyle(self.m)

    def hasByName(self, n):
        return True

    def getElementNames(self):
        return ("Standard",)

    def getCount(self):
        return 1

    def getByIndex(self, i):
        return _PageStyle(self.m)


class _Search:
    def __init__(self):
        self.SearchString = ""
        self.SearchCaseSensitive = False
        self.SearchWords = False
        self.SearchRegularExpression = False


class _Undo:
    def __init__(self, m):
        self.m = m

    def getAllUndoActionTitles(self):
        return tuple(reversed(self.m.ed.undo_names()))

    def isUndoPossible(self):
        return self.m.ed.can_undo()

    def undo(self):
        self.m.ed.undo()
        self.m.changed()

    def enterUndoContext(self, n):
        self.m.ed.begin_group(n)

    def leaveUndoContext(self):
        self.m.ed.end_group()


class _Controller:
    def __init__(self, m):
        self.m = m

    def getViewCursor(self):
        return _ViewCursor(self.m)

    def getSelection(self):
        m = self.m
        ed = m.ed
        pa, oa, pb, ob = ed.selection_range()
        r = _Range(m, (pa, oa), (pb, ob))
        n = ed.selection_count() if hasattr(ed, "selection_count") else 1
        return _Coll([r] * max(1, n))

    def select(self, r):
        if hasattr(r, "_select"):
            r._select()
            self.m.eng.view.after_move()
        return True

    def getViewSettings(self):
        class V:
            pass
        return V()


class NativeUnoModel:
    """getText(), getTextTables()... over Folio's own engine."""

    def __init__(self, eng):
        self.eng = eng

    @property
    def ed(self):
        return self.eng.ed

    def changed(self):
        self.eng.view.after_edit()

    def getText(self):
        return _Text(self)

    def getCurrentController(self):
        return _Controller(self)

    def getUndoManager(self):
        return _Undo(self)

    def isModified(self):
        return bool(self.ed.modified)

    def setModified(self, v):
        if not v and hasattr(self.ed, "set_modified"):
            self.ed.set_modified(False)

    def getTextTables(self):
        tabs = [_Table(self, ti, node) for k, node, ti in self.ed.body_blocks() if k == "t"]
        return _Coll(tabs, [t.getName() for t in tabs])

    def getTextFrames(self):
        return _Coll([])

    def getGraphicObjects(self):
        objs = [o for o in self.ed.objects_list() if o[2] in ("Picture",)]
        return _Coll(objs, [o[1] for o in objs])

    def getDrawPage(self):
        objs = self.ed.objects_list()
        return _Coll(objs, [o[1] for o in objs])

    def getDocumentIndexes(self):
        ed = self.ed
        out = []
        for depth, code, result in ed.fields_all():
            if code.strip().upper().startswith("TOC"):
                class Ix:
                    def __init__(self, r):
                        self.r = r

                    def getAnchor(self):
                        r = self.r

                        class A:
                            def getString(self):
                                return r
                        return A()

                    def update(self):
                        ed.update_toc()
                out.append(Ix(result))
        return _Coll(out)

    def getTextSections(self):
        return _Coll([])

    def getTextFields(self):
        class F:
            def __init__(self, code, result, comment=None):
                self.code, self.result = code, result
                self.Content = comment or ""
                self._c = comment is not None

            def supportsService(self, name):
                return self._c if name.endswith("Annotation") else not self._c

            def getPresentation(self, codes=False):
                return self.code if codes else self.result
        out = [F(c, r) for _d, c, r in self.ed.fields_all()]
        cm = getattr(getattr(self.eng, "win", None), "comments", None)
        cs = getattr(cm, "comments", None) or {}
        for c in (cs.values() if isinstance(cs, dict) else cs):
            text = c.get("text") if isinstance(c, dict) else getattr(c, "text", "")
            out.append(F("", "", text or ""))
        return _Coll(out)

    def getFootnotes(self):
        return _Coll(range(self.ed.note_count(False)))

    def getEndnotes(self):
        return _Coll(range(self.ed.note_count(True)))

    def getRedlines(self):
        return _Coll(self.ed.changes())

    def getStyleFamilies(self):
        from folio.native.uno_model import NativeModel
        fams = NativeModel(self.eng).getStyleFamilies()
        m = self

        class Fams:
            def getByName(self, fam):
                if fam == "PageStyles":
                    return _PageStyles(m)
                return fams.getByName(fam)

            def hasByName(self, fam):
                return fam == "PageStyles" or fams.hasByName(fam)

            def getElementNames(self):
                return tuple(fams.getElementNames()) + ("PageStyles",)
        return Fams()

    def getDocumentProperties(self):
        from folio.native.docprops import DocumentProperties
        return DocumentProperties(self.ed)

    def createSearchDescriptor(self):
        return _Search()

    def _hits(self, sd):
        opts = {"match_case": bool(sd.SearchCaseSensitive), "whole_word": bool(sd.SearchWords),
                "regex": bool(sd.SearchRegularExpression)}
        try:
            return self.ed.find_all(sd.SearchString, opts)
        except Exception:
            return []

    def findFirst(self, sd):
        h = self._hits(sd)
        return _Range(self, (h[0][0], h[0][1]), (h[0][2], h[0][3])) if h else None

    def findNext(self, after, sd):
        order = {p: i for i, p in enumerate(_paras(self.ed))}
        k = (order.get(after.a[0], 0), after.a[1])
        for pa, oa, pb, ob, _t in self._hits(sd):
            if (order.get(pa, 0), oa) >= k:
                return _Range(self, (pa, oa), (pb, ob))
        return None

    def findAll(self, sd):
        return _Coll([_Range(self, (h[0], h[1]), (h[2], h[3])) for h in self._hits(sd)])

    @property
    def RecordChanges(self):
        return self.ed.track_changes()

    @RecordChanges.setter
    def RecordChanges(self, v):
        self.ed.set_track_changes(bool(v))

    def __bool__(self):
        return True
