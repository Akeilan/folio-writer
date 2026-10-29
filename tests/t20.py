import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
import ctypes
CB = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_char_p, ctypes.c_void_p)
seen = []
def cb(t, payload, data):
    seen.append((t, (payload or b"")[:150]))
_cb = CB(cb)
REG = ctypes.CFUNCTYPE(None, ctypes.c_void_p, CB, ctypes.c_void_p)
def s0():
    office = win.engine.view.get_property("lopointer")
    log("office", office)
    pclass = ctypes.cast(ctypes.c_void_p(int(office)), ctypes.POINTER(ctypes.c_void_p))[0]
    slots = ctypes.cast(ctypes.c_void_p(pclass), ctypes.POINTER(ctypes.c_void_p))
    reg = REG(slots[6])   # nSize then slots
    reg(int(office), _cb, None)
    win.actions.insert_text("Hello")
def s1(): log("setoutline"); win.engine.command(".uno:SetOutline")
def s2(): log("survived", seen); app.quit()
steps(s0, s1, s2, delay=2500)
