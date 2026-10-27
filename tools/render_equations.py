#!/usr/bin/env python3
"""Build-time: render equation gallery previews to share/equations/*.png.

Starts a headless engine, puts every gallery formula on its own page of a
document, exports PDF, then crops each page to the formula."""
import os, subprocess, sys, tempfile, shutil, time
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "app"))
sys.path.append("/usr/lib/libreoffice/program")
from folio.eqn import galleries as G, unicodemath as U
import uno
from com.sun.star.beans import PropertyValue

OUT = os.path.join(HERE, "..", "share", "equations")
os.makedirs(OUT, exist_ok=True)
work = tempfile.mkdtemp(prefix="eqr-")
proc = subprocess.Popen(["soffice", "--headless", "--invisible", "--norestore",
                         "-env:UserInstallation=file://" + work + "/profile",
                         "--accept=socket,host=localhost,port=2099;urp;"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
local = uno.getComponentContext()
resolver = local.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", local)
for _ in range(60):
    try:
        ctx = resolver.resolve("uno:socket,host=localhost,port=2099;urp;StarOffice.ComponentContext")
        break
    except Exception:
        time.sleep(1)
smgr = ctx.ServiceManager
desktop = smgr.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
def pv(n, v):
    p = PropertyValue(); p.Name = n; p.Value = v; return p
doc = desktop.loadComponentFromURL("private:factory/swriter", "_blank", 0, (pv("Hidden", True),))
text = doc.getText()
cur = text.createTextCursor()
items = []
for name, its in G.GALLERIES:
    for iid, title, lin in its:
        if iid == "#" or not lin:
            continue
        try:
            sm = U.to_starmath(lin)
        except Exception as e:
            print("skip", iid, e); continue
        if items:
            cur.BreakType = uno.Enum("com.sun.star.style.BreakType", "PAGE_BEFORE")
        obj = doc.createInstance("com.sun.star.text.TextEmbeddedObject")
        obj.CLSID = "078B7ABA-54FC-457F-8551-6147e776a997"
        obj.AnchorType = uno.Enum("com.sun.star.text.TextContentAnchorType", "AS_CHARACTER")
        text.insertTextContent(cur, obj, False)
        emb = obj.getEmbeddedObject()
        emb.Formula = sm
        emb.BaseFontHeight = 20
        text.insertControlCharacter(cur, 0, False)
        cur.BreakType = uno.Enum("com.sun.star.style.BreakType", "NONE")
        items.append(iid)
pdf = os.path.join(work, "all.pdf")
doc.storeToURL(uno.systemPathToFileUrl(pdf), (pv("FilterName", "writer_pdf_Export"),))
doc.close(True)
try:
    desktop.terminate()
except Exception:
    pass
proc.wait(timeout=30)
subprocess.run(["pdftocairo", "-png", "-r", "150", pdf, os.path.join(work, "p")], check=True)
pages = sorted(f for f in os.listdir(work) if f.startswith("p-") and f.endswith(".png"))
print(len(items), "items,", len(pages), "pages")
ok = 0
for iid, pg in zip(items, pages):
    im = np.array(Image.open(os.path.join(work, pg)).convert("L"))
    dark = np.where(im < 245)
    if not len(dark[0]):
        print("empty", iid); continue
    t, b, l, r = dark[0].min(), dark[0].max(), dark[1].min(), dark[1].max()
    crop = im[max(0, t-4):b+5, max(0, l-4):r+5]
    a = (255 - crop.astype("int32")).clip(0, 255).astype("uint8")
    Image.fromarray(np.dstack([np.zeros_like(a), a]), "LA").save(os.path.join(OUT, iid + ".png"))
    ok += 1
print("rendered", ok)
shutil.rmtree(work, ignore_errors=True)
