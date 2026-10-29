"""Folio Page application: windows, recent files, settings."""
import json
import os
import subprocess
import sys

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("PangoCairo", "1.0")
from gi.repository import Gdk, Gio, GLib, Gtk  # noqa: E402

from . import APP_ID, APP_NAME, SHARE, VERSION  # noqa: E402

CONFIG = os.path.join(os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config"),
                      "folio-page")

def install_autocorrect(user):
    try:
        from .autocorrect import install
        install(user)
    except Exception as e:
        print("autocorrect:", e)


def prepare_engine_profile(profile, settings=None):
    """Folio's own data folder for the editor: the AutoCorrect lists."""
    user = os.path.join(profile, "user")
    os.makedirs(user, exist_ok=True)
    install_autocorrect(user)


def _paper_is_letter():
    try:
        out = subprocess.run(["locale", "-k", "LC_PAPER"], capture_output=True,
                             text=True, timeout=5).stdout
        return "height=279" in out
    except Exception:
        return False


class FolioApp(Gtk.Application):
    def __init__(self):
        Gtk.Application.__init__(self, application_id=APP_ID,
                                 flags=Gio.ApplicationFlags.HANDLES_OPEN)
        GLib.set_application_name(APP_NAME)
        GLib.set_prgname("folio-page")
        os.makedirs(CONFIG, exist_ok=True)
        self.engine_profile = os.path.join(CONFIG, "engine")
        self.settings_path = os.path.join(CONFIG, "settings.json")
        self.settings = self._load_settings()
        prepare_engine_profile(self.engine_profile, self.settings)
        from .widgets import set_units
        set_units(self.settings.get("units"))
        self.windows = []
        self._untitled = 0
        self.config_dir = CONFIG
        self.clip_history = []
        self._clip = None
        self.autorecover_dir = os.path.join(CONFIG, "autorecover")
        os.makedirs(self.autorecover_dir, exist_ok=True)

    # -------------------------------------------------------- settings
    def _load_settings(self):
        try:
            with open(self.settings_path, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            return {"recent": [], "author": os.environ.get("USER", "")}

    def save_settings(self):
        tmp = self.settings_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.settings, f, indent=1)
        os.replace(tmp, self.settings_path)

    def add_recent(self, path):
        path = os.path.abspath(path)
        rec = [p for p in self.settings.get("recent", []) if p != path]
        rec.insert(0, path)
        self.settings["recent"] = rec[:30]
        self.save_settings()
        try:
            Gtk.RecentManager.get_default().add_item("file://" + path)
        except Exception:
            pass

    def recent(self):
        n = self.settings.get("recent_count", 50)
        return [p for p in self.settings.get("recent", []) if os.path.exists(p)][:n]

    def pinned(self):
        return [p for p in self.settings.get("pinned", []) if os.path.exists(p)]

    def toggle_pin(self, path):
        pins = self.settings.get("pinned", [])
        if path in pins:
            pins.remove(path)
        else:
            pins.insert(0, path)
        self.settings["pinned"] = pins
        self.save_settings()

    def remove_recent(self, path):
        self.settings["recent"] = [p for p in self.settings.get("recent", []) if p != path]
        self.save_settings()

    def user_name(self):
        name = self.settings.get("user_name")
        if name:
            return name
        try:
            import pwd
            gecos = pwd.getpwuid(os.getuid()).pw_gecos.split(",")[0].strip()
            if gecos:
                return gecos
        except Exception:
            pass
        return os.environ.get("USER", "Author")

    def apply_settings(self):
        from .widgets import set_units
        set_units(self.settings.get("units"))
        prepare_engine_profile(self.engine_profile, self.settings)
        for w in self.windows:
            w.schedule_autorecover()
            w.apply_view_settings()
            try:
                w.build_qat()
                w.qat.show_all()
                w.status.apply_items()
            except Exception as e:
                print("apply settings:", e)
        self.apply_theme()

    def apply_theme(self):
        theme = self.settings.get("theme", "Colorful")
        screen = Gdk.Screen.get_default()
        for w in self.windows:
            ctx = w.get_style_context()
            for t in ("theme-darkgray", "theme-black", "theme-white"):
                ctx.remove_class(t)
            if theme != "Colorful":
                ctx.add_class("theme-" + theme.lower().replace(" ", ""))

    # -------------------------------------------------------- templates
    def user_template_path(self):
        name = "Normal-Letter.ott" if _paper_is_letter() else "Normal-A4.ott"
        return os.path.join(CONFIG, "templates", name)

    def normal_template(self):
        name = "Normal-Letter.ott" if _paper_is_letter() else "Normal-A4.ott"
        user = self.user_template_path()
        if os.path.exists(user):
            return user
        for base in (os.path.join(SHARE, "templates"),
                     os.path.join(os.path.dirname(__file__), "..", "..", "share", "templates")):
            p = os.path.join(base, name)
            if os.path.exists(p):
                return os.path.abspath(p)
        raise FileNotFoundError(name)

    def set_default_font(self, name, size, ed=None):
        """Set As Default: the Normal style of this document (ed) and of the
        Normal template."""
        from .native import edit_normal_template

        def fn(t):
            edits = []
            if name:
                edits.append(("w:rFonts", [("w:ascii", name), ("w:hAnsi", name), ("w:cs", name)]))
            if size:
                hp = str(int(round(float(size) * 2)))
                edits += [("w:sz", [("w:val", hp)]), ("w:szCs", [("w:val", hp)])]
            sid = {n: i for i, n in t.paragraph_styles()}.get("Normal", "Normal")
            t.style_apply_run(sid, edits)
        if ed is not None:
            ed.begin_group("Set As Default")
            try:
                fn(ed)
            finally:
                ed.end_group()
        try:
            edit_normal_template(self, fn)
        except Exception as e:
            print("default font:", e)

    def save_styles_as_default(self, engine):
        """New documents based on this template: the document's styles go into Normal."""
        import shutil
        import tempfile
        import zipfile
        from .native import normal_docx
        tmp = tempfile.mkdtemp(prefix="folio-styles-")
        try:
            cur = os.path.join(tmp, "doc.docx")
            engine.ed.save(cur)
            src, dst = normal_docx(self)
            with zipfile.ZipFile(cur) as z:
                styles = z.read("word/styles.xml")
                numbering = z.read("word/numbering.xml") if "word/numbering.xml" in z.namelist() else None
            with zipfile.ZipFile(src) as z:
                parts = {n: z.read(n) for n in z.namelist()}
            parts["word/styles.xml"] = styles
            if numbering is not None and "word/numbering.xml" in parts:
                parts["word/numbering.xml"] = numbering
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            out = dst + ".folio-tmp"
            with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("[Content_Types].xml", parts.pop("[Content_Types].xml"))
                for n, v in parts.items():
                    z.writestr(n, v)
            os.replace(out, dst)
        except Exception as e:
            print("save styles:", e)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def remember_style(self, name, family, props):
        # New documents based on the template: copy the whole style set over
        for w in self.windows:
            if getattr(w.engine, "ed", None) is not None:
                self.save_styles_as_default(w.engine)
                break

    # -------------------------------------------------------- autorecover
    def _recover_path(self, win):
        return os.path.join(self.autorecover_dir, "%s-%d.odt" % (
            "".join(c for c in win.doc_name() if c.isalnum() or c in " -_") or "Document",
            id(win) % 100000))

    def write_autorecover(self, win):
        p = self._recover_path(win)
        if win.engine.save_as(p, "odt", keep=False):
            with open(p + ".info", "w", encoding="utf-8") as f:
                json.dump({"name": win.doc_name(), "path": win.engine.path or ""}, f)

    def clear_autorecover(self, win):
        p = self._recover_path(win)
        for f in (p, p + ".info"):
            try:
                os.remove(f)
            except OSError:
                pass

    def recovered_files(self):
        out = []
        for f in sorted(os.listdir(self.autorecover_dir)):
            if f.endswith(".odt"):
                p = os.path.join(self.autorecover_dir, f)
                info = {}
                try:
                    with open(p + ".info", encoding="utf-8") as fh:
                        info = json.load(fh)
                except (OSError, ValueError):
                    pass
                out.append((p, info))
        return out

    def next_untitled(self):
        self._untitled += 1
        return "Document%d" % self._untitled

    # -------------------------------------------------------- windows
    def do_startup(self):
        Gtk.Application.do_startup(self)
        css = Gtk.CssProvider()
        css.load_from_path(os.path.join(os.path.dirname(__file__), "theme.css"))
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), css,
                                                 Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        from . import fontfix
        fontfix.install()

    def do_activate(self):
        if self.windows:
            self.windows[-1].present()
            return
        rec = self.recovered_files()
        win = self.new_window()
        script = os.environ.get("FOLIO_TEST_SCRIPT")
        if script:
            def run_script():
                ns = {"app": self, "win": win, "GLib": GLib, "Gtk": Gtk}
                with open(script) as f:
                    exec(compile(f.read(), script, "exec"), ns)
                return False
            GLib.timeout_add(6000, run_script)
        if rec:
            GLib.timeout_add(1500, self._offer_recovery, win, rec)

    def _offer_recovery(self, win, rec):
        names = ", ".join(info.get("name") or os.path.basename(p) for p, info in rec)
        if win.dialogs.confirm("%s recovered the following documents that weren't saved: %s.\n\n"
                               "Do you want to open them?" % (APP_NAME, names),
                               yes="Open", no="Discard", title="Document Recovery"):
            for p, info in rec:
                w = self.new_window(p)
                w.untitled = (info.get("name") or "Document") + " (Recovered)"
                w.engine.is_new = True
                GLib.timeout_add(1500, w.update_title)
        else:
            for p, _info in rec:
                for f in (p, p + ".info"):
                    try:
                        os.remove(f)
                    except OSError:
                        pass
        return False

    def do_open(self, files, n_files, hint):
        for f in files:
            path = f.get_path()
            if path:
                self.open_path(path)

    def new_window(self, path=None, template=None):
        from .window import DocWindow
        win = DocWindow(self, path, template)
        self.windows.append(win)
        self.apply_theme()
        win.present()
        return win

    def open_path(self, path, from_window=None):
        for w in self.windows:
            if w.engine.path == os.path.abspath(path):
                w.present()
                return w
        # reuse an untouched new document, as the reference app does
        if from_window is not None and from_window.engine.is_new and \
                not from_window.engine.modified:
            from_window.open_file(path)
            return from_window
        return self.new_window(path)

    def clipboard(self):
        if self._clip is None:
            from .clipboard import Clipboard
            self._clip = Clipboard()
        return self._clip

    def window_closed(self, win):
        try:
            self.save_settings()
        except OSError:
            pass
        if win in self.windows:
            self.windows.remove(win)
        if not self.windows:
            try:
                if self._clip is not None:
                    self._clip.keep_after_exit()
            except Exception:
                pass
            GLib.idle_add(self.quit)


MIME_DEFAULTS = [
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.template",
    "application/msword", "application/rtf", "text/rtf",
]


def make_default():
    for t in MIME_DEFAULTS:
        subprocess.run(["xdg-mime", "default", "folio-page.desktop", t],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def migrate_settings():
    """Folio Writer became Folio Page (2.33): the first start copies the old settings, recent files,
    templates, Quick Parts, sources and dictionaries over. The old folder stays as it was."""
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    old = os.path.join(base, "folio-writer")
    if os.path.isdir(old) and not os.path.exists(CONFIG):
        import shutil
        try:
            shutil.copytree(old, CONFIG, symlinks=True,
                            ignore=shutil.ignore_patterns("engine", "*.lock", "lock"))
        except Exception:
            pass


def main(argv=None):
    argv = list(argv if argv is not None else sys.argv)
    migrate_settings()
    if "--version" in argv:
        print("%s %s" % (APP_NAME, VERSION))
        return 0
    if "--make-default" in argv:
        make_default()
        print("%s is now the default for .docx, .doc, .dotx and .rtf files." % APP_NAME)
        return 0
    if "--reset-settings" in argv:
        import shutil
        for name in ("settings.json", "templates", "engine"):
            p = os.path.join(CONFIG, name)
            if os.path.isdir(p):
                shutil.rmtree(p, ignore_errors=True)
            elif os.path.exists(p):
                os.remove(p)
        print("Settings reset.")
        return 0
    app = FolioApp()
    if not app.settings.get("mime_registered_page") and os.path.exists(
            "/usr/share/applications/folio-page.desktop"):
        make_default()
        app.settings["mime_registered_page"] = True
        app.save_settings()
    code = app.run(argv)
    sys.stdout.flush()
    sys.stderr.flush()
    # Everything is saved by now; skip the engine's own (slow, noisy) teardown.
    os._exit(code or 0)
