"""X3-08: Folio Writer became Folio Page — names, and the first start carrying the old settings over.
Run: PYTHONPATH=app python3 tests/rename_test.py   (prints PASS/FAIL lines and a summary)"""
import json
import os
import sys
import tempfile

cfg = tempfile.mkdtemp()
os.environ["XDG_CONFIG_HOME"] = cfg
old = os.path.join(cfg, "folio-writer")
os.makedirs(os.path.join(old, "templates"))
with open(os.path.join(old, "settings.json"), "w") as f:
    json.dump({"recent": ["/home/u/letter.docx"], "mime_registered": True}, f)
with open(os.path.join(old, "dictionary.txt"), "w") as f:
    f.write("Shillings\n")
open(os.path.join(old, "templates", "Mine.dotx"), "w").close()
os.makedirs(os.path.join(old, "engine"))
sys.argv = ["folio-page", "--version"]
import folio  # noqa: E402
from folio import app  # noqa: E402

fails = 0


def check(name, cond, detail=""):
    global fails
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else "  " + repr(detail)))
    fails += 0 if cond else 1


check("app name", folio.APP_NAME == "Folio Page", folio.APP_NAME)
check("app id", folio.APP_ID == "org.folio.Page", folio.APP_ID)
check("config folder", app.CONFIG == os.path.join(cfg, "folio-page"), app.CONFIG)
app.migrate_settings()
new = os.path.join(cfg, "folio-page")
s = json.load(open(os.path.join(new, "settings.json")))
check("settings carried over", s.get("recent") == ["/home/u/letter.docx"], s)
check("dictionary carried over", open(os.path.join(new, "dictionary.txt")).read() == "Shillings\n")
check("templates carried over", os.path.exists(os.path.join(new, "templates", "Mine.dotx")))
check("engine cache not copied", not os.path.exists(os.path.join(new, "engine")))
check("old folder kept", os.path.exists(os.path.join(old, "settings.json")))
with open(os.path.join(new, "settings.json"), "w") as f:
    json.dump({"recent": []}, f)
app.migrate_settings()
check("second start leaves the new settings alone", json.load(open(os.path.join(new, "settings.json"))) == {"recent": []})
print("%d checks, %d failed" % (9, fails))
sys.exit(1 if fails else 0)
