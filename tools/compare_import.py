#!/usr/bin/env python3
"""Developer check: import files with Folio's own readers and render page 1 next to
LibreOffice's rendering of the same file. Run inside the build root:
  python3 tools/compare_import.py OUTDIR file...   (needs app/ on PYTHONPATH and folio_core)"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app"))
from folio.native import importers  # noqa: E402
import folio_core  # noqa: E402

out = sys.argv[1]
os.makedirs(out, exist_ok=True)
for f in sys.argv[2:]:
    base = os.path.splitext(os.path.basename(f))[0].replace(" ", "_")
    try:
        dx = os.path.join(out, base + ".docx")
        importers.to_docx(f, dx)
        ed = folio_core.Editor.open(dx)
        pdf = os.path.join(out, base + ".folio.pdf")
        ed.export_pdf(pdf)
        print("OK", f, ed.page_count())
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("FAIL", f, e)
