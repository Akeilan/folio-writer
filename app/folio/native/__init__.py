"""Folio's own document engine (folio_core, written in Rust): the .docx is
the document model, laid out with the original's rules and drawn here."""
import importlib.machinery
import importlib.util
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_CANDIDATES = [
    os.environ.get("FOLIO_CORE_LIB", ""),
    # next to the code (installed), else a development checkout
    os.path.join(_HERE, "..", "..", "folio_core.so"),
    os.path.normpath(os.path.join(_HERE, "..", "..", "..", "core", "target", "release",
                                  "libfolio_core.so")),
    "/usr/lib/folio-writer/folio_core.so",
]

_core = None


def core():
    """The folio_core module, or None if it isn't installed."""
    global _core
    if _core is not None:
        return _core
    if "folio_core" in sys.modules:
        _core = sys.modules["folio_core"]
        return _core
    for path in _CANDIDATES:
        if path and os.path.exists(path):
            loader = importlib.machinery.ExtensionFileLoader("folio_core", path)
            spec = importlib.util.spec_from_file_location("folio_core", path, loader=loader)
            mod = importlib.util.module_from_spec(spec)
            try:
                loader.exec_module(mod)
            except ImportError as e:
                print("folio_core:", e)
                continue
            sys.modules["folio_core"] = mod
            _core = mod
            return mod
    return None


def available():
    return core() is not None


def wanted(settings):
    """Does the user want the new engine (Options > Advanced, or
    FOLIO_ENGINE=native)?"""
    env = os.environ.get("FOLIO_ENGINE")
    if env:
        return env == "native"
    return settings.get("engine") == "native"
