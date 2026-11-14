import os as _o; TESTS = _o.environ["FOLIO_WRITER_TESTS"]; exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read()); exec(open("/tmp/p5/probes/ph.py").read())
import subprocess
def a():
    yield 0.5
    win.open_file("/tmp/corpus/scripts.docx"); yield 2.0
    win.engine.save_as("/tmp/p5out/cjk.pdf", keep=False); yield 0.5
    t = subprocess.run(["pdftotext", "/tmp/p5out/cjk.pdf", "-"], capture_output=True, text=True).stdout
    for w in ("Ελληνικά", "Русский", "中文测试文本", "日本語", "한국어", "العربية", "עברית", "Emoji", "é ñ ö"):
        check("pdf text has %s" % w, w in t)
    note("pdf text", repr(t[:700]))
    note("fonts", subprocess.run(["pdffonts", "/tmp/p5out/cjk.pdf"], capture_output=True, text=True).stdout.replace("\n", " | ")[:600])
    shot("cjk")
run_scenarios(a)
