exec(open("/home/claude/folio2/tests/common.py").read())
A = win.actions; m = lambda: win.engine.model
def s0(): A.insert_text("Page one"); win.engine.command(".uno:InsertPagebreak"); A.insert_text("Page two"); win.engine.command(".uno:InsertPagebreak"); A.insert_text("Page three")
def s1():
    import json, subprocess
    eng = win.engine; doc = eng._doc_ptr()
    from folio.engine import file_url
    opts = json.dumps({"PageRange": {"type": "string", "value": "2-3"}, "ExportBookmarks": {"type":"boolean","value":"true"}})
    ok = doc.contents.pClass.contents.saveAs(doc, file_url("/tmp/x.pdf").encode(), b"pdf", opts.encode())
    log("ok", ok, subprocess.run(["pdfinfo","/tmp/x.pdf"],capture_output=True,text=True).stdout)
def s2(): app.quit()
steps(s0, s1, s2, delay=1500)
