#!/usr/bin/env python3
"""Build the blank-document templates the new engine starts from:
share/templates/Normal-Letter.docx and Normal-A4.docx, with the original's
default formatting (Calibri 11 pt body, Calibri Light headings, 8 pt after,
1.08 line spacing) and its built-in style set."""
import os
import sys
import zipfile

W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" ' \
    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
HDR = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n'

CONTENT_TYPES = HDR + (
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
    '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
    '<Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>'
    '<Override PartName="/word/fontTable.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.fontTable+xml"/>'
    '<Override PartName="/word/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>'
    '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
    '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
    '</Types>')

ROOT_RELS = HDR + (
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>'
    '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
    '</Relationships>')

DOC_RELS = HDR + (
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
    '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/>'
    '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/fontTable" Target="fontTable.xml"/>'
    '<Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="theme/theme1.xml"/>'
    '</Relationships>')


def document(w, h):
    return HDR + (
        '<w:document %s><w:body><w:p/>'
        '<w:sectPr><w:pgSz w:w="%d" w:h="%d"/>'
        '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="720" '
        'w:footer="720" w:gutter="0"/><w:cols w:space="720"/><w:docGrid w:linePitch="360"/>'
        '</w:sectPr></w:body></w:document>' % (W, w, h))


def style(kind, sid, name, body="", based=None, nxt=None, link=None, default=False, q=True,
          ui=None, hidden=False):
    s = '<w:style w:type="%s"%s w:styleId="%s"><w:name w:val="%s"/>' % (
        kind, ' w:default="1"' if default else "", sid, name)
    if based:
        s += '<w:basedOn w:val="%s"/>' % based
    if nxt:
        s += '<w:next w:val="%s"/>' % nxt
    if link:
        s += '<w:link w:val="%s"/>' % link
    if ui is not None:
        s += '<w:uiPriority w:val="%d"/>' % ui
    if hidden:
        s += '<w:semiHidden/><w:unhideWhenUsed/>'
    if q:
        s += '<w:qFormat/>'
    return s + body + '</w:style>'


def heading(n, before, color, sz, italic=False):
    rpr = '<w:rFonts w:asciiTheme="majorHAnsi" w:eastAsiaTheme="majorEastAsia" ' \
          'w:hAnsiTheme="majorHAnsi" w:cstheme="majorBidi"/>'
    if italic:
        rpr += '<w:i/><w:iCs/>'
    rpr += '<w:color w:val="%s"/>' % color
    if sz:
        rpr += '<w:sz w:val="%d"/><w:szCs w:val="%d"/>' % (sz, sz)
    ppr = '<w:pPr><w:keepNext/><w:keepLines/><w:spacing w:before="%d" w:after="0"/>' \
          '<w:outlineLvl w:val="%d"/></w:pPr>' % (before, n - 1)
    return style("paragraph", "Heading%d" % n, "heading %d" % n, ppr + '<w:rPr>%s</w:rPr>' % rpr,
                 based="Normal", nxt="Normal", link="Heading%dChar" % n, ui=9) + \
        style("character", "Heading%dChar" % n, "Heading %d Char" % n,
              '<w:rPr>%s</w:rPr>' % rpr, based="DefaultParagraphFont", link="Heading%d" % n,
              ui=9, q=False)


def styles():
    s = HDR + '<w:styles %s>' % W
    s += ('<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:asciiTheme="minorHAnsi" '
          'w:eastAsiaTheme="minorHAnsi" w:hAnsiTheme="minorHAnsi" w:cstheme="minorBidi"/>'
          '<w:sz w:val="22"/><w:szCs w:val="22"/><w:lang w:val="en-US" w:eastAsia="en-US" '
          'w:bidi="ar-SA"/></w:rPr></w:rPrDefault><w:pPrDefault><w:pPr>'
          '<w:spacing w:after="160" w:line="259" w:lineRule="auto"/></w:pPr></w:pPrDefault>'
          '</w:docDefaults>')
    s += style("paragraph", "Normal", "Normal", default=True, ui=0)
    for n, (b, c, sz, it) in enumerate([(240, "2E6B3F", 32, False), (40, "2E6B3F", 26, False),
                                        (40, "1F4D2C", 24, False), (40, "2E6B3F", 0, True),
                                        (40, "2E6B3F", 0, False), (40, "1F4D2C", 0, False),
                                        (40, "1F4D2C", 0, True), (40, "272727", 21, False),
                                        (40, "272727", 21, True)], 1):
        s += heading(n, b, c, sz, it)
    s += style("character", "DefaultParagraphFont", "Default Paragraph Font", default=True,
               ui=1, hidden=True, q=False)
    s += style("table", "TableNormal", "Normal Table",
               '<w:tblPr><w:tblInd w:w="0" w:type="dxa"/><w:tblCellMar><w:top w:w="0" '
               'w:type="dxa"/><w:left w:w="108" w:type="dxa"/><w:bottom w:w="0" w:type="dxa"/>'
               '<w:right w:w="108" w:type="dxa"/></w:tblCellMar></w:tblPr>',
               default=True, ui=99, hidden=True, q=False)
    s += style("numbering", "NoList", "No List", default=True, ui=99, hidden=True, q=False)
    major = ('<w:rFonts w:asciiTheme="majorHAnsi" w:eastAsiaTheme="majorEastAsia" '
             'w:hAnsiTheme="majorHAnsi" w:cstheme="majorBidi"/>')
    s += style("paragraph", "Title", "Title",
               '<w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/>'
               '<w:contextualSpacing/></w:pPr><w:rPr>%s<w:spacing w:val="-10"/>'
               '<w:kern w:val="28"/><w:sz w:val="56"/><w:szCs w:val="56"/></w:rPr>' % major,
               based="Normal", nxt="Normal", link="TitleChar", ui=10)
    s += style("character", "TitleChar", "Title Char",
               '<w:rPr>%s<w:spacing w:val="-10"/><w:kern w:val="28"/><w:sz w:val="56"/>'
               '<w:szCs w:val="56"/></w:rPr>' % major, based="DefaultParagraphFont",
               link="Title", ui=10, q=False)
    sub = ('<w:rFonts w:eastAsiaTheme="minorEastAsia"/><w:color w:val="5A5A5A" '
           'w:themeColor="text1" w:themeTint="A5"/><w:spacing w:val="15"/>')
    s += style("paragraph", "Subtitle", "Subtitle",
               '<w:pPr><w:numPr><w:ilvl w:val="1"/></w:numPr></w:pPr><w:rPr>%s</w:rPr>' % sub,
               based="Normal", nxt="Normal", link="SubtitleChar", ui=11)
    s += style("character", "SubtitleChar", "Subtitle Char", '<w:rPr>%s</w:rPr>' % sub,
               based="DefaultParagraphFont", link="Subtitle", ui=11, q=False)
    s += style("paragraph", "NoSpacing", "No Spacing",
               '<w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/></w:pPr>', ui=1)
    s += style("character", "SubtleEmphasis", "Subtle Emphasis",
               '<w:rPr><w:i/><w:iCs/><w:color w:val="404040" w:themeColor="text1" '
               'w:themeTint="BF"/></w:rPr>', based="DefaultParagraphFont", ui=19)
    s += style("character", "Emphasis", "Emphasis", '<w:rPr><w:i/><w:iCs/></w:rPr>',
               based="DefaultParagraphFont", ui=20)
    s += style("character", "IntenseEmphasis", "Intense Emphasis",
               '<w:rPr><w:i/><w:iCs/><w:color w:val="4472C4" w:themeColor="accent1"/></w:rPr>',
               based="DefaultParagraphFont", ui=21)
    s += style("character", "Strong", "Strong", '<w:rPr><w:b/><w:bCs/></w:rPr>',
               based="DefaultParagraphFont", ui=22)
    q = ('<w:rPr><w:i/><w:iCs/><w:color w:val="404040" w:themeColor="text1" '
         'w:themeTint="BF"/></w:rPr>')
    s += style("paragraph", "Quote", "Quote",
               '<w:pPr><w:spacing w:before="200" w:after="160"/><w:ind w:left="864" '
               'w:right="864"/><w:jc w:val="center"/></w:pPr>' + q,
               based="Normal", nxt="Normal", link="QuoteChar", ui=29)
    s += style("character", "QuoteChar", "Quote Char", q, based="DefaultParagraphFont",
               link="Quote", ui=29, q=False)
    iq = '<w:rPr><w:i/><w:iCs/><w:color w:val="4472C4" w:themeColor="accent1"/></w:rPr>'
    s += style("paragraph", "IntenseQuote", "Intense Quote",
               '<w:pPr><w:pBdr><w:top w:val="single" w:sz="4" w:space="10" w:color="4472C4" '
               'w:themeColor="accent1"/><w:bottom w:val="single" w:sz="4" w:space="10" '
               'w:color="4472C4" w:themeColor="accent1"/></w:pBdr><w:spacing w:before="360" '
               'w:after="360"/><w:ind w:left="864" w:right="864"/><w:jc w:val="center"/>'
               '</w:pPr>' + iq, based="Normal", nxt="Normal", link="IntenseQuoteChar", ui=30)
    s += style("character", "IntenseQuoteChar", "Intense Quote Char", iq,
               based="DefaultParagraphFont", link="IntenseQuote", ui=30, q=False)
    s += style("character", "SubtleReference", "Subtle Reference",
               '<w:rPr><w:smallCaps/><w:color w:val="5A5A5A" w:themeColor="text1" '
               'w:themeTint="A5"/></w:rPr>', based="DefaultParagraphFont", ui=31)
    s += style("character", "IntenseReference", "Intense Reference",
               '<w:rPr><w:b/><w:bCs/><w:smallCaps/><w:color w:val="4472C4" '
               'w:themeColor="accent1"/><w:spacing w:val="5"/></w:rPr>',
               based="DefaultParagraphFont", ui=32)
    s += style("character", "BookTitle", "Book Title",
               '<w:rPr><w:b/><w:bCs/><w:i/><w:iCs/><w:spacing w:val="5"/></w:rPr>',
               based="DefaultParagraphFont", ui=33)
    s += style("paragraph", "ListParagraph", "List Paragraph",
               '<w:pPr><w:ind w:left="720"/><w:contextualSpacing/></w:pPr>',
               based="Normal", ui=34)
    s += style("paragraph", "Caption", "caption",
               '<w:pPr><w:spacing w:after="200" w:line="240" w:lineRule="auto"/></w:pPr>'
               '<w:rPr><w:i/><w:iCs/><w:color w:val="44546A" w:themeColor="text2"/>'
               '<w:sz w:val="18"/><w:szCs w:val="18"/></w:rPr>',
               based="Normal", nxt="Normal", ui=35, hidden=True)
    s += style("paragraph", "TOCHeading", "TOC Heading",
               '<w:pPr><w:outlineLvl w:val="9"/></w:pPr>',
               based="Heading1", nxt="Normal", ui=39, hidden=True)
    hf = ('<w:pPr><w:tabs><w:tab w:val="center" w:pos="4680"/><w:tab w:val="right" '
          'w:pos="9360"/></w:tabs><w:spacing w:after="0" w:line="240" w:lineRule="auto"/>'
          '</w:pPr>')
    for sid, nm in (("Header", "header"), ("Footer", "footer")):
        s += style("paragraph", sid, nm, hf, based="Normal", link=sid + "Char", ui=99,
                   hidden=True, q=False)
        s += style("character", sid + "Char", nm.capitalize() + " Char", "",
                   based="DefaultParagraphFont", link=sid, ui=99, q=False)
    s += style("character", "Hyperlink", "Hyperlink",
               '<w:rPr><w:color w:val="0563C1" w:themeColor="hyperlink"/>'
               '<w:u w:val="single"/></w:rPr>', based="DefaultParagraphFont", ui=99,
               hidden=True, q=False)
    s += style("table", "TableGrid", "Table Grid",
               '<w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/></w:pPr>'
               '<w:tblPr><w:tblBorders>' + "".join(
                   '<w:%s w:val="single" w:sz="4" w:space="0" w:color="auto"/>' % b
                   for b in ("top", "left", "bottom", "right", "insideH", "insideV")) +
               '</w:tblBorders></w:tblPr>', based="TableNormal", ui=39, q=False)
    return s + '</w:styles>'


SETTINGS = HDR + (
    '<w:settings %s><w:zoom w:percent="100"/><w:proofState w:spelling="clean" w:grammar="clean"/>'
    '<w:defaultTabStop w:val="720"/><w:characterSpacingControl w:val="doNotCompress"/>'
    '<w:compat><w:compatSetting w:name="compatibilityMode" w:uri="http://schemas.microsoft.com/office/word" w:val="15"/>'
    '<w:compatSetting w:name="overrideTableStyleFontSizeAndJustification" w:uri="http://schemas.microsoft.com/office/word" w:val="1"/>'
    '<w:compatSetting w:name="enableOpenTypeFeatures" w:uri="http://schemas.microsoft.com/office/word" w:val="1"/>'
    '<w:compatSetting w:name="doNotFlipMirrorIndents" w:uri="http://schemas.microsoft.com/office/word" w:val="1"/>'
    '<w:compatSetting w:name="differentiateMultirowTableHeaders" w:uri="http://schemas.microsoft.com/office/word" w:val="1"/>'
    '</w:compat><w:themeFontLang w:val="en-US"/><w:decimalSymbol w:val="."/><w:listSeparator w:val=","/>'
    '</w:settings>' % W)

FONTS = HDR + (
    '<w:fonts %s>'
    '<w:font w:name="Calibri"><w:panose1 w:val="020F0502020204030204"/><w:charset w:val="00"/>'
    '<w:family w:val="swiss"/><w:pitch w:val="variable"/></w:font>'
    '<w:font w:name="Times New Roman"><w:panose1 w:val="02020603050405020304"/><w:charset w:val="00"/>'
    '<w:family w:val="roman"/><w:pitch w:val="variable"/></w:font>'
    '<w:font w:name="Calibri Light"><w:panose1 w:val="020F0302020204030204"/><w:charset w:val="00"/>'
    '<w:family w:val="swiss"/><w:pitch w:val="variable"/></w:font>'
    '</w:fonts>' % W)

THEME = HDR + (
    '<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Office Theme">'
    '<a:themeElements><a:clrScheme name="Office">'
    '<a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1>'
    '<a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1>'
    '<a:dk2><a:srgbClr val="44546A"/></a:dk2><a:lt2><a:srgbClr val="E7E6E6"/></a:lt2>'
    '<a:accent1><a:srgbClr val="4472C4"/></a:accent1><a:accent2><a:srgbClr val="ED7D31"/></a:accent2>'
    '<a:accent3><a:srgbClr val="A5A5A5"/></a:accent3><a:accent4><a:srgbClr val="FFC000"/></a:accent4>'
    '<a:accent5><a:srgbClr val="5B9BD5"/></a:accent5><a:accent6><a:srgbClr val="70AD47"/></a:accent6>'
    '<a:hlink><a:srgbClr val="0563C1"/></a:hlink><a:folHlink><a:srgbClr val="954F72"/></a:folHlink>'
    '</a:clrScheme><a:fontScheme name="Office">'
    '<a:majorFont><a:latin typeface="Calibri Light" panose="020F0302020204030204"/>'
    '<a:ea typeface=""/><a:cs typeface=""/></a:majorFont>'
    '<a:minorFont><a:latin typeface="Calibri" panose="020F0502020204030204"/>'
    '<a:ea typeface=""/><a:cs typeface=""/></a:minorFont></a:fontScheme>'
    '<a:fmtScheme name="Office"><a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
    '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
    '</a:fillStyleLst><a:lnStyleLst><a:ln w="6350"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>'
    '<a:ln w="12700"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>'
    '<a:ln w="19050"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst>'
    '<a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/></a:effectStyle>'
    '<a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst>'
    '<a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
    '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
    '</a:bgFillStyleLst></a:fmtScheme></a:themeElements></a:theme>')

CORE = HDR + (
    '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
    'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
    'xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
    '<dc:title></dc:title><dc:creator></dc:creator><cp:revision>1</cp:revision></cp:coreProperties>')

APP = HDR + (
    '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
    'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
    '<Template>Normal.dotm</Template><TotalTime>0</TotalTime><Pages>1</Pages><Words>0</Words>'
    '<Characters>0</Characters><Application>Folio Page</Application><DocSecurity>0</DocSecurity>'
    '<Lines>1</Lines><Paragraphs>1</Paragraphs><ScaleCrop>false</ScaleCrop>'
    '<LinksUpToDate>false</LinksUpToDate><CharactersWithSpaces>0</CharactersWithSpaces>'
    '<SharedDoc>false</SharedDoc><HyperlinksChanged>false</HyperlinksChanged><AppVersion>16.0000</AppVersion>'
    '</Properties>')


def build(path, w, h):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("_rels/.rels", ROOT_RELS)
        z.writestr("word/document.xml", document(w, h))
        z.writestr("word/_rels/document.xml.rels", DOC_RELS)
        z.writestr("word/styles.xml", styles())
        z.writestr("word/settings.xml", SETTINGS)
        z.writestr("word/fontTable.xml", FONTS)
        z.writestr("word/theme/theme1.xml", THEME)
        z.writestr("docProps/core.xml", CORE)
        z.writestr("docProps/app.xml", APP)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(__file__), "..", "share", "templates")
    build(os.path.join(out, "Normal-Letter.docx"), 12240, 15840)
    build(os.path.join(out, "Normal-A4.docx"), 11906, 16838)
    print("written to", os.path.abspath(out))
