#!/bin/bash
# Rebuild the 22.04 test machine at /srv/jammy from the Ubuntu archive.
set -e
export DEBIAN_FRONTEND=noninteractive
apt-get install -y -q debootstrap rsync xdotool >/dev/null
R=/srv/jammy
[ -x $R/usr/bin/apt-get ] || debootstrap --variant=minbase --components=main,universe jammy $R http://archive.ubuntu.com/ubuntu >/tmp/debootstrap.log 2>&1
cat > $R/etc/apt/sources.list <<S
deb http://archive.ubuntu.com/ubuntu jammy main universe
deb http://archive.ubuntu.com/ubuntu jammy-updates main universe
deb http://archive.ubuntu.com/ubuntu jammy-security main universe
S
mountpoint -q $R/proc || mount -t proc proc $R/proc
mountpoint -q $R/dev || mount --rbind /dev $R/dev
mountpoint -q $R/sys || mount --rbind /sys $R/sys
mkdir -p $R/tmp/.X11-unix; mountpoint -q $R/tmp/.X11-unix || mount --bind /tmp/.X11-unix $R/tmp/.X11-unix
cp /etc/resolv.conf $R/etc/resolv.conf
for v in http_proxy https_proxy HTTP_PROXY HTTPS_PROXY no_proxy; do [ -n "${!v:-}" ] && echo "export $v='${!v}'"; done > $R/root/proxyenv.sh
[ -n "${http_proxy:-${HTTP_PROXY:-}}" ] && echo "Acquire::http::Proxy \"${http_proxy:-$HTTP_PROXY}\";" > $R/etc/apt/apt.conf.d/99proxy
chroot $R bash -c "apt-get update -q >/dev/null && apt-get install -y -q --no-install-recommends \
  python3 python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-poppler-0.18 python3-enchant python3-pil librsvg2-common \
  fonts-crosextra-carlito fonts-crosextra-caladea fonts-liberation2 hunspell-en-us mythes-en-us hyphen-en-us \
  fonts-dejavu-extra fonts-lmodern xdotool x11-utils dbus-x11 at-spi2-core adwaita-icon-theme gnome-themes-extra \
  build-essential pkg-config libfreetype-dev libcairo2-dev python3-dev ca-certificates curl poppler-utils \
  libgtk-3-0 xdg-utils python3-cairo imagemagick unzip zip" > /tmp/jammy-apt.log 2>&1 || { tail -5 /tmp/jammy-apt.log; exit 1; }
rsync -a /root/.cargo /root/.rustup $R/root/
echo 'export PATH=/root/.cargo/bin:$PATH SSL_CERT_FILE=/root/.ccr/ca-bundle.crt CARGO_HTTP_CAINFO=/root/.ccr/ca-bundle.crt; . /root/proxyenv.sh' > $R/root/cargoenv.sh
mkdir -p $R/root/.ccr; cp -r /root/.ccr/. $R/root/.ccr/ 2>/dev/null || true
echo "jammy ready: $(chroot $R python3 -c 'import gi; gi.require_version("Gtk","3.0"); from gi.repository import Gtk; print("gtk", Gtk.get_minor_version())')"
