#!/bin/bash
# Build folio-page_<version>_<arch>.deb and the transitional folio-writer_<version>_all.deb
# (Folio Writer became Folio Page in 2.33).
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
VERSION=$(sed -n 's/^VERSION *= *"\(.*\)"/\1/p' "$HERE/app/folio/__init__.py")
OUT=${OUT:-$HERE/../build}
ROOT=$(mktemp -d)
mkdir -p "$OUT"

# generated resources (only rebuilt when missing)
[ -d "$HERE/share/equations" ] || python3 "$HERE/tools/render_equations.py"
[ -d "$HERE/share/templates/gallery" ] || python3 "$HERE/tools/make_gallery.py"

# application code
mkdir -p "$ROOT/usr/lib/folio-page"
(cd "$HERE/app" && find folio -name '*.py' -o -name '*.css' -o -name '*.svg' | while read -r f; do
   install -Dm644 "$f" "$ROOT/usr/lib/folio-page/$f"; done)
install -Dm755 "$HERE/bin/folio-page" "$ROOT/usr/bin/folio-page"
ln -s folio-page "$ROOT/usr/bin/folio"
# the old command keeps working for scripts and the other Folio apps
ln -s folio-page "$ROOT/usr/bin/folio-writer"

# the document engine (native code)
ARCH=all
CORE_SO="$HERE/core/target/release/libfolio_core.so"
if [ "${NO_CORE:-}" != 1 ]; then
  (cd "$HERE/core" && ./build-jammy.sh >/dev/null 2>&1) || true
fi
if [ -f "$CORE_SO" ]; then
  install -Dm644 "$CORE_SO" "$ROOT/usr/lib/folio-page/folio_core.so"
  strip --strip-unneeded "$ROOT/usr/lib/folio-page/folio_core.so"
  ARCH=amd64
fi

# shared data
S="$ROOT/usr/share/folio-page"
install -Dm644 "$HERE/share/templates/Normal-A4.ott" "$S/templates/Normal-A4.ott"
install -Dm644 "$HERE/share/templates/Normal-Letter.ott" "$S/templates/Normal-Letter.ott"
python3 "$HERE/tools/make_normal_docx.py" "$HERE/share/templates" >/dev/null
install -Dm644 "$HERE/share/templates/Normal-A4.docx" "$S/templates/Normal-A4.docx"
install -Dm644 "$HERE/share/templates/Normal-Letter.docx" "$S/templates/Normal-Letter.docx"
for f in "$HERE"/share/templates/gallery/*; do
  install -Dm644 "$f" "$S/templates/gallery/$(basename "$f")"
done
for f in "$HERE"/share/equations/*.png; do
  install -Dm644 "$f" "$S/equations/$(basename "$f")"
done
install -Dm644 "$HERE/share/inkmath/templates.json" "$S/inkmath/templates.json"
install -Dm644 "$HERE/share/inkmath/handwriting.json" "$S/inkmath/handwriting.json"
install -Dm644 "$HERE/share/inkmath/prior.json" "$S/inkmath/prior.json"
for f in "$HERE"/share/autocorr/*.dat; do install -Dm644 "$f" "$S/autocorr/$(basename "$f")"; done
install -Dm644 "$HERE/share/SHORTCUTS.txt" "$S/SHORTCUTS.txt"
# ribbon icons drawn from the Colibre set (MPL 2.0 / CC BY-SA 4.0), recoloured at load
install -Dm644 "$HERE/share/iconset/colibre_svg.zip" "$S/iconset/colibre_svg.zip"
install -Dm644 "$HERE/share/iconset/COLIBRE-COPYRIGHT.txt" "$ROOT/usr/share/doc/folio-page/COLIBRE-COPYRIGHT.txt"
# the equation font (STIX Two Math, SIL OFL)
install -Dm644 "$HERE/share/fonts/STIX2Math.otf" "$S/fonts/STIX2Math.otf"
install -Dm644 "$HERE/share/fonts/STIX-OFL.txt" "$ROOT/usr/share/doc/folio-page/STIX-OFL.txt"
install -Dm644 "$HERE/share/61-folio-page-aliases.conf" "$ROOT/usr/share/fontconfig/conf.avail/61-folio-page-aliases.conf"
mkdir -p "$ROOT/etc/fonts/conf.d"
ln -s ../../../usr/share/fontconfig/conf.avail/61-folio-page-aliases.conf "$ROOT/etc/fonts/conf.d/61-folio-page-aliases.conf"
install -Dm644 "$HERE/share/folio-page.desktop" "$ROOT/usr/share/applications/folio-page.desktop"
# the old desktop id stays (hidden) so file-type defaults and dock pins made for it keep working
install -Dm644 "$HERE/share/folio-writer.desktop" "$ROOT/usr/share/applications/folio-writer.desktop"
for n in folio-page folio-writer; do
  install -Dm644 "$HERE/share/icons/folio-page.svg" "$ROOT/usr/share/icons/hicolor/scalable/apps/$n.svg"
  for s in 16 24 32 48 64 128 256; do
    install -Dm644 "$HERE/share/icons/folio-page-$s.png" "$ROOT/usr/share/icons/hicolor/${s}x${s}/apps/$n.png"
  done
done
install -Dm644 "$HERE/share/SHORTCUTS.txt" "$ROOT/usr/share/doc/folio-page/SHORTCUTS.txt"
install -Dm644 "$HERE/share/copyright" "$ROOT/usr/share/doc/folio-page/copyright"
install -Dm644 "$HERE/share/folio-page.1" "$ROOT/usr/share/man/man1/folio-page.1"
gzip -9n "$ROOT/usr/share/man/man1/folio-page.1"
ln -s folio-page.1.gz "$ROOT/usr/share/man/man1/folio.1.gz"
ln -s folio-page.1.gz "$ROOT/usr/share/man/man1/folio-writer.1.gz"

# control
mkdir -p "$ROOT/DEBIAN"
SIZE=$(du -sk "$ROOT" | cut -f1)
cat > "$ROOT/DEBIAN/control" <<CTRL
Package: folio-page
Version: $VERSION
Replaces: folio-writer (<< 2.33.0)
Breaks: folio-writer (<< 2.33.0)
Section: editors
Priority: optional
Architecture: $ARCH
Installed-Size: $SIZE
Depends: python3 (>= 3.10), libc6 (>= 2.34), libcairo2, libfreetype6, python3-gi, python3-gi-cairo, gir1.2-gtk-3.0, gir1.2-poppler-0.18, python3-enchant, python3-pil, librsvg2-common, fonts-crosextra-carlito, fonts-crosextra-caladea, fonts-liberation2 | fonts-liberation
Recommends: hunspell-en-us | hunspell-dictionary, mythes-en-us, hyphen-en-us, cups-client, xdg-utils, fonts-dejavu-extra, fonts-lmodern, python3-speechd, speech-dispatcher, espeak-ng
Suggests: libreoffice-writer
Maintainer: Ron Shillings <ron.shillings@gmail.com>
Description: ribbon word processor (formerly Folio Writer)
 Folio Page is a word processor with a ribbon interface, KeyTips, a File
 view, the standard desktop word-processor keyboard shortcuts, a linear-format
 equation editor and .docx as its native format.
CTRL
cat > "$ROOT/DEBIAN/postinst" <<'PI'
#!/bin/sh
set -e
if [ "$1" = "configure" ]; then
  command -v update-desktop-database >/dev/null && update-desktop-database -q /usr/share/applications || true
  command -v gtk-update-icon-cache >/dev/null && gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor || true
  command -v fc-cache >/dev/null && fc-cache -s >/dev/null 2>&1 || true
  /usr/bin/python3 -m compileall -q /usr/lib/folio-page >/dev/null 2>&1 || true
fi
exit 0
PI
cat > "$ROOT/DEBIAN/prerm" <<'PR'
#!/bin/sh
set -e
find /usr/lib/folio-page -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
exit 0
PR
cat > "$ROOT/DEBIAN/postrm" <<'PR'
#!/bin/sh
set -e
if [ "$1" = "remove" ] || [ "$1" = "purge" ]; then
  command -v update-desktop-database >/dev/null && update-desktop-database -q /usr/share/applications || true
  command -v gtk-update-icon-cache >/dev/null && gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor || true
fi
exit 0
PR
chmod 755 "$ROOT/DEBIAN/postinst" "$ROOT/DEBIAN/postrm" "$ROOT/DEBIAN/prerm"
find "$ROOT" -type d -exec chmod 755 {} +
dpkg-deb --root-owner-group --build -Zxz "$ROOT" "$OUT/folio-page_${VERSION}_${ARCH}.deb" >/dev/null
rm -rf "$ROOT"

# transitional package: folio-writer moves people over to folio-page
T=$(mktemp -d)
mkdir -p "$T/DEBIAN" "$T/usr/share/doc/folio-writer"
cat > "$T/usr/share/doc/folio-writer/README.Debian" <<'TXT'
Folio Writer is now called Folio Page. This package only installs folio-page and can be removed.
The folio-writer command keeps working; it opens Folio Page.
TXT
install -Dm644 "$HERE/share/copyright" "$T/usr/share/doc/folio-writer/copyright"
cat > "$T/DEBIAN/control" <<CTRL
Package: folio-writer
Version: $VERSION
Section: oldlibs
Priority: optional
Architecture: all
Depends: folio-page (>= $VERSION)
Maintainer: Ron Shillings <ron.shillings@gmail.com>
Description: transitional package: Folio Writer is now Folio Page
 Folio Writer was renamed Folio Page. This empty package installs folio-page;
 it can be removed afterwards.
CTRL
find "$T" -type d -exec chmod 755 {} +
dpkg-deb --root-owner-group --build -Zxz "$T" "$OUT/folio-writer_${VERSION}_all.deb" >/dev/null
rm -rf "$T"
echo "$OUT/folio-writer_${VERSION}_all.deb"
echo "$OUT/folio-page_${VERSION}_${ARCH}.deb"
