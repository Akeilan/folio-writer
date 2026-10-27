#!/usr/bin/env python3
"""Build-time: the template gallery shown under File > New, with thumbnails.
Each template starts from the Normal template so styles match."""
import os, subprocess, sys, tempfile, time, shutil
import uno
from com.sun.star.beans import PropertyValue
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "share", "templates", "Normal-Letter.ott")
OUT = os.path.join(HERE, "..", "share", "templates", "gallery")
os.makedirs(OUT, exist_ok=True)
work = tempfile.mkdtemp(prefix="gal-")
proc = subprocess.Popen(["soffice", "--headless", "--invisible", "--norestore",
                         "-env:UserInstallation=file://" + work + "/p",
                         "--accept=socket,host=localhost,port=2097;urp;"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
local = uno.getComponentContext()
res = local.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", local)
for _ in range(60):
    try:
        ctx = res.resolve("uno:socket,host=localhost,port=2097;urp;StarOffice.ComponentContext"); break
    except Exception:
        time.sleep(1)
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
def pv(n, v):
    p = PropertyValue(); p.Name = n; p.Value = v; return p
PT = 2540 / 72.0
ACCENT = 0x2F5496

def new_doc():
    return desktop.loadComponentFromURL(uno.systemPathToFileUrl(os.path.abspath(SRC)), "_blank", 0,
                                        (pv("Hidden", True), pv("AsTemplate", True)))

class W:
    def __init__(self, doc):
        self.doc = doc; self.text = doc.getText(); self.cur = self.text.createTextCursor()
        self.first = True
    def p(self, txt, style="Standard", **props):
        if not self.first:
            self.text.insertControlCharacter(self.cur, 0, False)
        self.first = False
        self.cur.ParaStyleName = style
        for k in ("CharColor", "CharWeight", "ParaAdjust", "CharHeight", "ParaBottomMargin",
                  "ParaTopMargin", "CharPosture"):
            try:
                self.cur.setPropertyToDefault(k)
            except Exception:
                pass
        start = self.cur.getEnd()
        self.text.insertString(self.cur, txt, False)
        if props:
            c = self.text.createTextCursorByRange(self.cur)
            c.gotoStartOfParagraph(True)
            for k, v in props.items():
                setattr(c, k, v)
        return self

def save(doc, name):
    path = os.path.join(OUT, name + ".ott")
    doc.storeToURL(uno.systemPathToFileUrl(os.path.abspath(path)), (pv("FilterName", "writer8_template"),))
    pdf = os.path.join(work, name + ".pdf")
    doc.storeToURL(uno.systemPathToFileUrl(pdf), (pv("FilterName", "writer_pdf_Export"),
                                                  pv("FilterData", (pv("PageRange", "1"),))))
    doc.close(True)
    subprocess.run(["pdftocairo", "-png", "-singlefile", "-scale-to", "300", pdf,
                    os.path.join(OUT, name)], check=True)

LOREM = ("Replace this text with your own. To change how the text looks, pick a style on the "
         "Home tab: Heading 1 for section titles, Normal for body text.")

# 1. Single spaced
d = new_doc(); st = d.getStyleFamilies().getByName("ParagraphStyles").getByName("Standard")
ls = uno.createUnoStruct("com.sun.star.style.LineSpacing"); ls.Mode = 0; ls.Height = 100
st.ParaLineSpacing = ls; st.ParaBottomMargin = 0
save(d, "Single spaced (blank)")

# 2. Report
d = new_doc(); w = W(d)
w.p("Report Title", "Title").p("Subtitle or date", "Subtitle")
w.p("Introduction", "Heading 1").p(LOREM).p("Findings", "Heading 1").p(LOREM)
w.p("Details", "Heading 2").p(LOREM).p("Conclusion", "Heading 1").p(LOREM)
save(d, "Report")

# 3. Letter
d = new_doc(); w = W(d)
w.p("Your Name", CharHeight=16.0, CharColor=ACCENT, CharWeight=150.0)
w.p("Street Address | City, State ZIP | Phone | Email", CharColor=0x595959)
w.p("").p("Date").p("").p("Recipient Name").p("Title").p("Company").p("Street Address").p("City, State ZIP")
w.p("").p("Dear Recipient Name,").p(LOREM).p(LOREM).p("Sincerely,").p("").p("Your Name")
save(d, "Letter")

# 4. Resume
d = new_doc(); w = W(d)
w.p("YOUR NAME", "Title", CharColor=ACCENT)
w.p("Address · Phone · Email · Website", CharColor=0x595959)
w.p("Objective", "Heading 1").p("Describe the kind of role you're looking for in a sentence or two.")
w.p("Experience", "Heading 1").p("Job Title, Company", "Heading 2").p("Dates From – To", CharColor=0x595959)
w.p("Summarize your key responsibilities, leadership and most stellar accomplishments.")
w.p("Education", "Heading 1").p("Degree, School", "Heading 2").p("Month Year", CharColor=0x595959)
w.p("Skills", "Heading 1").p("List your strengths relevant to the role you're applying for.")
save(d, "Resume")

# 5. Memo
d = new_doc(); w = W(d)
w.p("MEMO", "Title", CharColor=ACCENT)
for k in ("To:", "From:", "CC:", "Date:", "Re:"):
    w.p("%s\t[%s]" % (k, k.rstrip(":")))
w.p("").p(LOREM).p(LOREM)
save(d, "Memo")

# 6. Meeting minutes
d = new_doc(); w = W(d)
w.p("Meeting Minutes", "Title").p("Date · Time · Location", "Subtitle")
w.p("Attendees", "Heading 1").p("Names of attendees")
w.p("Agenda", "Heading 1").p("Item one").p("Item two")
w.p("Decisions", "Heading 1").p("What was decided.")
w.p("Action Items", "Heading 1").p("Who does what, by when.")
save(d, "Meeting minutes")

try:
    desktop.terminate()
except Exception:
    pass
proc.wait(timeout=30)
shutil.rmtree(work, ignore_errors=True)
print(sorted(os.listdir(OUT)))
