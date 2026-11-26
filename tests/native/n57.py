import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
# 2.39 (W5-04): a chart in an .odt comes in as a chart, rebuilt from its own data, rather than
# being left out with a note. Made by hand the way LibreOffice writes one, and, where LibreOffice
# is installed, a chart Page made, taken through LibreOffice and back.
import os
import shutil
import subprocess
import zipfile

ODT = "/tmp/n57.odt"
NS = ('xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
      'xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0" '
      'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" '
      'xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" '
      'xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0" '
      'xmlns:chart="urn:oasis:names:tc:opendocument:xmlns:chart:1.0" '
      'xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0" '
      'xmlns:xlink="http://www.w3.org/1999/xlink" '
      'xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0" office:version="1.3"')


def cell(v):
    if isinstance(v, (int, float)):
        return '<table:table-cell office:value-type="float" office:value="%s"><text:p>%s</text:p></table:table-cell>' % (v, v)
    return '<table:table-cell office:value-type="string"><text:p>%s</text:p></table:table-cell>' % v


def chart_xml(cls, title, series, cats, values, vertical=False, stacked=False, legend="end"):
    """A chart object's content.xml, as LibreOffice writes it: the series point into its own table."""
    rows = "".join("<table:table-row>%s</table:table-row>" % "".join(cell(x) for x in [c] + list(v))
                   for c, v in zip(cats, values))
    cols = "ABCDEFGH"
    n = len(cats) + 1
    sers = "".join('<chart:series chart:style-name="ch5" chart:values-cell-range-address="local-table.$%s$2:.$%s$%d" '
                   'chart:label-cell-address="local-table.$%s$1" chart:class="chart:%s"/>'
                   % (cols[i + 1], cols[i + 1], n, cols[i + 1], cls) for i in range(len(series)))
    head = "<table:table-row>%s</table:table-row>" % "".join(cell(x) for x in [""] + list(series))
    return ('<?xml version="1.0" encoding="UTF-8"?><office:document-content %s>'
            '<office:automatic-styles>'
            '<style:style style:name="ch4" style:family="chart"><style:chart-properties chart:vertical="%s" chart:stacked="%s"/></style:style>'
            '<style:style style:name="ch5" style:family="chart"><style:chart-properties chart:symbol-type="none"/></style:style>'
            '</office:automatic-styles><office:body><office:chart>'
            '<chart:chart svg:width="16cm" svg:height="9cm" chart:class="chart:%s">'
            '<chart:title><text:p>%s</text:p></chart:title>%s'
            '<chart:plot-area chart:style-name="ch4">'
            '<chart:axis chart:dimension="x" chart:name="primary-x"><chart:categories table:cell-range-address="local-table.$A$2:.$A$%d"/></chart:axis>'
            '<chart:axis chart:dimension="y" chart:name="primary-y"><chart:grid chart:class="major"/></chart:axis>'
            '%s</chart:plot-area>'
            '<table:table table:name="local-table"><table:table-header-columns><table:table-column/></table:table-header-columns>'
            '<table:table-columns><table:table-column table:number-columns-repeated="%d"/></table:table-columns>'
            '<table:table-header-rows>%s</table:table-header-rows><table:table-rows>%s</table:table-rows></table:table>'
            '</chart:chart></office:chart></office:body></office:document-content>'
            % (NS, "true" if vertical else "false", "true" if stacked else "false", cls, title,
               '<chart:legend chart:legend-position="%s"/>' % legend if legend else "", n, sers, len(series), head, rows))


def make_odt():
    charts = [
        ("Object 1", chart_xml("bar", "Sales by quarter", ["North", "South"], ["Q1", "Q2", "Q3"],
                               [[10, 4], [12.5, 6], [9, 8]])),
        ("Object 2", chart_xml("line", "Visitors", ["2025"], ["Jan", "Feb", "Mar", "Apr"], [[3], [5], [4], [7]], legend=None)),
        ("Object 3", chart_xml("circle", "Share", ["Share"], ["Tea", "Coffee"], [[40], [60]], legend="bottom")),
        ("Object 4", chart_xml("bar", "Across", ["A", "B"], ["x", "y"], [[1, 2], [3, 4]], vertical=True, stacked=True)),
    ]
    frames = "".join('<text:p>Chart %d:<draw:frame draw:name="%s" text:anchor-type="as-char" svg:width="16cm" svg:height="9cm">'
                     '<draw:object xlink:href="./%s" xlink:type="simple"/>'
                     '<draw:image xlink:href="./ObjectReplacements/%s" xlink:type="simple"/></draw:frame></text:p>'
                     % (i + 1, n, n, n) for i, (n, _x) in enumerate(charts))
    content = ('<?xml version="1.0" encoding="UTF-8"?><office:document-content %s><office:body><office:text>'
               '<text:p>Before the charts.</text:p>%s<text:p>After the charts.</text:p></office:text></office:body>'
               '</office:document-content>' % (NS, frames))
    man = ['<manifest:file-entry manifest:full-path="/" manifest:media-type="application/vnd.oasis.opendocument.text"/>',
           '<manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/>']
    with zipfile.ZipFile(ODT, "w") as z:
        z.writestr("mimetype", "application/vnd.oasis.opendocument.text", compress_type=zipfile.ZIP_STORED)
        z.writestr("content.xml", content)
        for n, x in charts:
            z.writestr(n + "/content.xml", x)
            z.writestr("ObjectReplacements/" + n, b"VCLMTF\x01\x00 not a picture anything else can draw")
            man.append('<manifest:file-entry manifest:full-path="%s/" manifest:media-type="application/vnd.oasis.opendocument.chart"/>' % n)
        z.writestr("META-INF/manifest.xml", '<?xml version="1.0" encoding="UTF-8"?><manifest:manifest '
                   'xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0" manifest:version="1.3">%s'
                   '</manifest:manifest>' % "".join(man))


def parts(ed, name):
    ed.save(name)
    z = zipfile.ZipFile(name)
    return {n: z.read(n) for n in z.namelist()}


def models(px):
    from folio.native import charts
    return [charts.read(px[n].decode("utf-8")) for n in sorted(px) if n.startswith("word/charts/chart") and n.endswith(".xml")]


def a():
    yield 1.0
    make_odt()
    win.engine.open(ODT); yield 3.0
    px = parts(E.ed, "/tmp/n57.docx")
    ms = models(px)
    check("four charts come in as charts", len(ms) == 4, len(ms))
    if len(ms) == 4:
        m = ms[0]
        check("a clustered column chart, its title and legend", m["type"] == 0 and m["title"] == "Sales by quarter"
              and m["legend"] == "right", (m["type"], m["title"], m["legend"]))
        check("its series, categories and values", m["data"]["cols"] == ["North", "South"] and
              m["data"]["rows"] == ["Q1", "Q2", "Q3"] and m["data"]["values"] == [[10, 4], [12.5, 6], [9, 8]], m["data"])
        check("value gridlines kept", m["grid"][0] is True, m["grid"])
        check("a line chart with no legend", ms[1]["type"] == 3 and ms[1]["legend"] == "none"
              and [v[0] for v in ms[1]["data"]["values"]] == [3, 5, 4, 7], (ms[1]["type"], ms[1]["legend"]))
        check("a pie", ms[2]["type"] == 5 and ms[2]["legend"] == "bottom" and ms[2]["data"]["rows"] == ["Tea", "Coffee"], ms[2]["type"])
        check("stacked bars that run across", ms[3]["type"] == 10, ms[3]["type"])
        check("each with its workbook", sum(1 for n in px if n.startswith("word/embeddings/") and n.endswith(".xlsx")) == 4)
    doc = px.get("word/document.xml", b"").decode("utf-8", "replace")
    check("the words around them are there too", "Before the charts." in doc and "After the charts." in doc)
    note = getattr(win.engine, "import_note", None) or ""
    check("nothing is reported as left out", "embedded object" not in note, note)
    E.ed.mark_saved()
    # a chart Page made, through LibreOffice and back
    if shutil.which("soffice") and len(ms) == 4:
        od = "/tmp/n57_lo"
        shutil.rmtree(od, ignore_errors=True)
        subprocess.run(["timeout", "240", "soffice", "-env:UserInstallation=file:///tmp/n57_prof", "--headless",
                        "--convert-to", "odt", "--outdir", od, "/tmp/n57.docx"], capture_output=True)
        lo = os.path.join(od, "n57.odt")
        check("LibreOffice made an .odt of it", os.path.exists(lo))
        if os.path.exists(lo):
            win.engine.open(lo); yield 3.0
            back = models(parts(E.ed, "/tmp/n57_back.docx"))
            check("LibreOffice's charts come back as charts", len(back) == 4, len(back))
            if back:
                check("with the same series and values", back[0]["data"]["cols"] == ["North", "South"]
                      and back[0]["data"]["values"] == [[10, 4], [12.5, 6], [9, 8]], back[0]["data"])
            E.ed.mark_saved()


run_scenarios(a)
