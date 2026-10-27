#!/bin/bash
# Build folio-writer_<version>_all.deb
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
mkdir -p "$ROOT/usr/lib/folio-writer"
(cd "$HERE/app" && find folio -name '*.py' -o -name '*.css' -o -name '*.svg' | while read -r f; do
   install -Dm644 "$f" "$ROOT/usr/lib/folio-writer/$f"; done)
install -Dm755 "$HERE/bin/folio-writer" "$ROOT/usr/bin/folio-writer"
ln -s folio-writer "$ROOT/usr/bin/folio"

# the document engine (native code)
ARCH=all
CORE_SO="$HERE/core/target/release/libfolio_core.so"
if [ "${NO_CORE:-}" != 1 ]; then
  (cd "$HERE/core" && ./build-jammy.sh >/dev/null 2>&1) || true
fi
if [ -f "$CORE_SO" ]; then
  install -Dm644 "$CORE_SO" "$ROOT/usr/lib/folio-writer/folio_core.so"
  strip --strip-unneeded "$ROOT/usr/lib/folio-writer/folio_core.so"
  ARCH=amd64
fi

# shared data
S="$ROOT/usr/share/folio-writer"
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
install -Dm644 "$HERE/share/iconset/COLIBRE-COPYRIGHT.txt" "$ROOT/usr/share/doc/folio-writer/COLIBRE-COPYRIGHT.txt"
# the equation font (STIX Two Math, SIL OFL)
install -Dm644 "$HERE/share/fonts/STIX2Math.otf" "$S/fonts/STIX2Math.otf"
install -Dm644 "$HERE/share/fonts/STIX-OFL.txt" "$ROOT/usr/share/doc/folio-writer/STIX-OFL.txt"
install -Dm644 "$HERE/share/61-folio-writer-aliases.conf" "$ROOT/usr/share/fontconfig/conf.avail/61-folio-writer-aliases.conf"
mkdir -p "$ROOT/etc/fonts/conf.d"
ln -s ../../../usr/share/fontconfig/conf.avail/61-folio-writer-aliases.conf "$ROOT/etc/fonts/conf.d/61-folio-writer-aliases.conf"
install -Dm644 "$HERE/share/folio-writer.desktop" "$ROOT/usr/share/applications/folio-writer.desktop"
install -Dm644 "$HERE/share/icons/folio-writer.svg" "$ROOT/usr/share/icons/hicolor/scalable/apps/folio-writer.svg"
for s in 16 24 32 48 64 128 256; do
  install -Dm644 "$HERE/share/icons/folio-writer-$s.png" "$ROOT/usr/share/icons/hicolor/${s}x${s}/apps/folio-writer.png"
done
install -Dm644 "$HERE/share/SHORTCUTS.txt" "$ROOT/usr/share/doc/folio-writer/SHORTCUTS.txt"
install -Dm644 "$HERE/share/copyright" "$ROOT/usr/share/doc/folio-writer/copyright"
install -Dm644 "$HERE/share/folio-writer.1" "$ROOT/usr/share/man/man1/folio-writer.1"
gzip -9n "$ROOT/usr/share/man/man1/folio-writer.1"
ln -s folio-writer.1.gz "$ROOT/usr/share/man/man1/folio.1.gz"

# control
mkdir -p "$ROOT/DEBIAN"
SIZE=$(du -sk "$ROOT" | cut -f1)
cat > "$ROOT/DEBIAN/control" <<CTRL
Package: folio-writer
Version: $VERSION
Section: editors
Priority: optional
Architecture: $ARCH
Installed-Size: $SIZE
Depends: python3 (>= 3.10), libc6 (>= 2.34), libcairo2, libfreetype6, python3-gi, python3-gi-cairo, gir1.2-gtk-3.0, gir1.2-poppler-0.18, python3-enchant, python3-pil, librsvg2-common, fonts-crosextra-carlito, fonts-crosextra-caladea, fonts-liberation2 | fonts-liberation
Recommends: hunspell-en-us | hunspell-dictionary, mythes-en-us, hyphen-en-us, cups-client, xdg-utils, fonts-dejavu-extra, fonts-lmodern, python3-speechd, speech-dispatcher, espeak-ng
Suggests: libreoffice-writer, python3-uno, gir1.2-lokdocview-0.1, libreoffice-lightproof-en
Maintainer: Ron Shillings <ron.shillings@gmail.com>
Description: ribbon word processor
 Folio Writer is a word processor with a ribbon interface, KeyTips, a File
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
  /usr/bin/python3 -m compileall -q /usr/lib/folio-writer >/dev/null 2>&1 || true
fi
exit 0
PI
cat > "$ROOT/DEBIAN/prerm" <<'PR'
#!/bin/sh
set -e
find /usr/lib/folio-writer -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
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
dpkg-deb --root-owner-group --build -Zxz "$ROOT" "$OUT/folio-writer_${VERSION}_${ARCH}.deb" >/dev/null
rm -rf "$ROOT"
echo "$OUT/folio-writer_${VERSION}_${ARCH}.deb"
