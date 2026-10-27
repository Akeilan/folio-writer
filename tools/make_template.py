#!/usr/bin/env python3
"""Build the Normal templates (A4 and Letter) with Word's default look:
11 pt body text, 8 pt after, 1.08 line spacing, blue headings, 1" margins.
Run with LibreOffice's python and a headless office listening on port 2002.
usage: make_template.py OUTDIR
"""
import sys, os, time, subprocess, tempfile, uno
from com.sun.star.beans import PropertyValue
from com.sun.star.style.LineSpacingMode import PROP
from com.sun.star.style.ParagraphAdjust import LEFT, CENTER

OUT = os.path.abspath(sys.argv[1])
os.makedirs(OUT, exist_ok=True)

FONT = "Carlito"
HEAD_FONT = "Carlito"
BLUE = 0x2F5496
DARK_BLUE = 0x1F3763
PT = 35.278  # 1/100 mm per point


def pv(n, v):
    p = PropertyValue()
    p.Name = n
    p.Value = v
    return p


def ls(pct):
    s = uno.createUnoStruct("com.sun.star.style.LineSpacing")
    s.Mode = PROP
    s.Height = pct
    return s


profile = tempfile.mkdtemp(prefix="folio-tpl-")
proc = subprocess.Popen(
    ["soffice", "--headless", "--invisible", "--norestore", "--nologo",
     "-env:UserInstallation=file://" + profile,
     "--accept=socket,host=localhost,port=2011;urp;"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
local = uno.getComponentContext()
res = local.ServiceManager.createInstanceWithContext(
    "com.sun.star.bridge.UnoUrlResolver", local)
for _ in range(90):
    try:
        ctx = res.resolve(
            "uno:socket,host=localhost,port=2011;urp;StarOffice.ComponentContext")
        break
    except Exception:
        time.sleep(1)
else:
    proc.kill()
    sys.exit("could not start office")

desk = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)


def setp(obj, **kw):
    for k, v in kw.items():
        try:
            obj.setPropertyValue(k, v)
        except Exception as e:
            print("  ! %s.%s: %s" % (obj.getName() if hasattr(obj, "getName") else obj, k, e))


def build(paper, w, h):
    doc = desk.loadComponentFromURL("private:factory/swriter", "_blank", 0,
                                    (pv("Hidden", True),))
    fam = doc.getStyleFamilies()
    para = fam.getByName("ParagraphStyles")
    char = fam.getByName("CharacterStyles")
    page = fam.getByName("PageStyles")

    defaults = doc.createInstance("com.sun.star.text.Defaults")
    setp(defaults, TabStopDistance=1270, CharFontName=FONT, CharHeight=11.0,
         CharFontNameAsian=FONT, CharFontNameComplex=FONT,
         ParaBottomMargin=int(8 * PT), ParaLineSpacing=ls(108))

    body = dict(CharFontName=FONT, CharFontFamily=5, CharHeight=11.0,
                CharFontNameAsian=FONT, CharFontNameComplex=FONT,
                CharHeightAsian=11.0, CharHeightComplex=11.0,
                ParaTopMargin=0, ParaBottomMargin=int(8 * PT),
                ParaLineSpacing=ls(108), ParaOrphans=2, ParaWidows=2)
    setp(para.getByName("Standard"), **body)
    # "Body Text" matches Normal, like Word's Body Text (adds 6 pt after).
    setp(para.getByName("Text body"), ParaTopMargin=0,
         ParaBottomMargin=int(6 * PT), ParaLineSpacing=ls(108))

    setp(para.getByName("Heading"), CharFontName=HEAD_FONT, CharHeight=16.0,
         CharWeight=100.0, ParaTopMargin=int(12 * PT), ParaBottomMargin=0,
         ParaLineSpacing=ls(108), ParaKeepTogether=True, CharColor=BLUE)
    heads = {
        1: dict(CharHeight=16.0, CharColor=BLUE, ParaTopMargin=int(12 * PT)),
        2: dict(CharHeight=13.0, CharColor=BLUE, ParaTopMargin=int(2 * PT)),
        3: dict(CharHeight=12.0, CharColor=DARK_BLUE, ParaTopMargin=int(2 * PT)),
        4: dict(CharHeight=11.0, CharColor=BLUE, CharPosture=uno.Enum("com.sun.star.awt.FontSlant", "ITALIC"), ParaTopMargin=int(2 * PT)),
        5: dict(CharHeight=11.0, CharColor=BLUE, ParaTopMargin=int(2 * PT)),
        6: dict(CharHeight=11.0, CharColor=DARK_BLUE, ParaTopMargin=int(2 * PT)),
        7: dict(CharHeight=11.0, CharColor=DARK_BLUE, CharPosture=uno.Enum("com.sun.star.awt.FontSlant", "ITALIC"), ParaTopMargin=int(2 * PT)),
        8: dict(CharHeight=10.5, CharColor=0x272727, ParaTopMargin=int(2 * PT)),
        9: dict(CharHeight=10.5, CharColor=0x272727, CharPosture=uno.Enum("com.sun.star.awt.FontSlant", "ITALIC"), ParaTopMargin=int(2 * PT)),
    }
    for n, props in heads.items():
        st = para.getByName("Heading %d" % n)
        props.update(CharFontName=HEAD_FONT, CharWeight=100.0, CharWeightAsian=100.0,
                     CharWeightComplex=100.0, ParaBottomMargin=0,
                     ParaLineSpacing=ls(108), ParaKeepTogether=True,
                     FollowStyle="Standard")
        if "CharPosture" not in props:
            props["CharPosture"] = uno.Enum("com.sun.star.awt.FontSlant", "NONE")
        setp(st, **props)

    setp(para.getByName("Title"), CharFontName=HEAD_FONT, CharHeight=28.0,
         CharWeight=100.0, CharKerning=-18, ParaAdjust=LEFT,
         ParaTopMargin=0, ParaBottomMargin=0, ParaLineSpacing=ls(100),
         CharColor=0x000000, FollowStyle="Standard")
    setp(para.getByName("Subtitle"), CharFontName=FONT, CharHeight=11.0,
         CharKerning=26, ParaAdjust=LEFT, CharColor=0x5A5A5A,
         ParaTopMargin=0, ParaBottomMargin=int(8 * PT), FollowStyle="Standard")
    try:
        setp(para.getByName("Quotations"), CharFontName=FONT,
             CharPosture=uno.Enum("com.sun.star.awt.FontSlant", "ITALIC"),
             CharColor=0x404040, ParaAdjust=CENTER, ParaLeftMargin=1524,
             ParaRightMargin=1524, ParaTopMargin=int(10 * PT),
             ParaBottomMargin=int(8 * PT))
    except Exception:
        pass
    for name in ("Header", "Footer"):
        try:
            setp(para.getByName(name), ParaBottomMargin=0, ParaTopMargin=0,
                 ParaLineSpacing=ls(100))
        except Exception:
            pass
    for name in ("Footnote", "Endnote"):
        try:
            setp(para.getByName(name), CharHeight=10.0, ParaBottomMargin=0,
                 ParaLineSpacing=ls(100), ParaLeftMargin=0, ParaFirstLineIndent=0)
        except Exception:
            pass
    # Word's standard styles that the engine does not have built in
    def new_para(name, parent="Standard", **props):
        if not para.hasByName(name):
            st = doc.createInstance("com.sun.star.style.ParagraphStyle")
            para.insertByName(name, st)
        st = para.getByName(name)
        try:
            st.ParentStyle = parent
        except Exception:
            pass
        setp(st, **props)
        return st

    def new_char(name, **props):
        if not char.hasByName(name):
            st = doc.createInstance("com.sun.star.style.CharacterStyle")
            char.insertByName(name, st)
        st = char.getByName(name)
        setp(st, **props)
        return st

    ITALIC = uno.Enum("com.sun.star.awt.FontSlant", "ITALIC")
    new_para("No Spacing", ParaBottomMargin=0, ParaTopMargin=0,
             ParaLineSpacing=ls(100))
    new_para("List Paragraph", ParaLeftMargin=1270, ParaContextMargin=True)
    q = new_para("Intense Quote", CharPosture=ITALIC, CharColor=BLUE,
                 ParaAdjust=CENTER, ParaLeftMargin=864, ParaRightMargin=864,
                 ParaTopMargin=int(18 * PT), ParaBottomMargin=int(18 * PT))
    try:
        line = uno.createUnoStruct("com.sun.star.table.BorderLine2")
        line.LineWidth = 18
        line.Color = BLUE
        q.TopBorder = line
        q.BottomBorder = line
        q.TopBorderDistance = int(10 * PT)
        q.BottomBorderDistance = int(10 * PT)
    except Exception:
        pass
    # Word's "TOC Heading" is the built-in Contents Heading (renamed in the UI)
    setp(para.getByName("Contents Heading"), CharFontName=HEAD_FONT,
         CharHeight=16.0, CharColor=BLUE, CharWeight=100.0,
         ParaTopMargin=int(12 * PT), ParaBottomMargin=0)
    new_char("Subtle Emphasis", CharPosture=ITALIC, CharColor=0x404040)
    new_char("Intense Emphasis", CharPosture=ITALIC, CharColor=BLUE)
    new_char("Subtle Reference", CharCaseMap=4, CharColor=0x5A5A5A)
    new_char("Intense Reference", CharCaseMap=4, CharWeight=150.0,
             CharColor=BLUE, CharKerning=9)
    new_char("Book Title", CharWeight=150.0, CharPosture=ITALIC, CharKerning=9)
    for name in ("Strong Emphasis",):
        if char.hasByName(name):
            setp(char.getByName(name), CharWeight=150.0)

    for name in ("Internet link", "Internet Link"):
        if char.hasByName(name):
            setp(char.getByName(name), CharColor=0x0563C1)
    for name in ("Visited Internet Link", "Visited Internet link"):
        if char.hasByName(name):
            setp(char.getByName(name), CharColor=0x954F72)

    pg = page.getByName("Standard")
    setp(pg, Width=w, Height=h, LeftMargin=2540, RightMargin=2540,
         TopMargin=2540, BottomMargin=2540)

    # Word-compatible layout behaviour for new documents.
    settings = doc.createInstance("com.sun.star.text.DocumentSettings")
    for k, v in dict(AddParaTableSpacing=True, AddParaSpacingToTableCells=True,
                     ParaSpaceMax=True, ParaSpaceMaxAtPages=True,
                     TabOverMargin=True, TabOverflow=True,
                     UseFormerLineSpacing=False, AddExternalLeading=True,
                     ApplyParagraphMarkFormatToNumbering=True,
                     MathBaselineAlignment=True).items():
        try:
            settings.setPropertyValue(k, v)
        except Exception:
            pass
    props = doc.getDocumentProperties()
    props.Title = ""
    url = uno.systemPathToFileUrl(os.path.join(OUT, "Normal-%s.ott" % paper))
    doc.storeToURL(url, (pv("FilterName", "writer8_template"),))
    doc.close(True)
    print("wrote", url)


try:
    build("A4", 21000, 29700)
    build("Letter", 21590, 27940)
finally:
    try:
        desk.terminate()
    except Exception:
        pass
    try:
        proc.wait(30)
    except Exception:
        proc.kill()
