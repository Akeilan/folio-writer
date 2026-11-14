# probe helpers: exec'd into a probe after common.py / wc.py
import re as _re, zipfile, json
_w = open(TESTS + "/native_command_walk.py").read()
exec(_w[_w.index("def name_of(c):"):_w.index("\ndef walk(")])
_ITEMS = {}
def _load_items():
    _ITEMS.clear()
    for tab, label, fn in items_of():
        _ITEMS.setdefault(label, []).append((tab, fn))
def R(label, tab=None):
    """Press a ribbon control or gallery item by its label, as a click would."""
    if not _ITEMS: _load_items()
    c = [x for x in _ITEMS.get(label, []) if tab is None or x[0] == tab]
    if not c:
        _load_items()
        c = [x for x in _ITEMS.get(label, []) if tab is None or x[0] == tab]
    if not c:
        raise KeyError("no ribbon control %r" % label)
    c[0][1]()
    pump(0.15)
def ed(): return win.engine.ed
def doc_xml(path=None):
    p = path or "/tmp/p5out/_ph_%d.docx" % os.getpid()
    if path is None: ed().save(p)
    with zipfile.ZipFile(p) as z:
        return {n: z.read(n).decode("utf8", "replace") for n in z.namelist() if n.endswith(".xml") or n.endswith(".rels")}
def cnt(xml, tag):
    return len(_re.findall(r"<%s[ />]" % _re.escape(tag), xml))
def body_text():
    return _re.sub(r"<[^>]+>", "", _re.sub(r"</w:p>", "\n", doc_xml()["word/document.xml"]))
_K0, _T0 = K, T
def K(*specs):
    _K0(*specs); pump(0.12)
def T(text, delay=8):
    _T0(text, delay); pump(0.15 + 0.004 * len(text))
