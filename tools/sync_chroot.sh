#!/bin/bash
# copy the Writer tree into the 22.04 build root at /tmp/fw (and /src/fwc for the engine)
set -e
R=/srv/jammy
mountpoint -q $R/proc || mount -t proc proc $R/proc
mountpoint -q $R/dev || mount --rbind /dev $R/dev
mountpoint -q $R/sys || mount --rbind /sys $R/sys
pgrep -x Xvfb >/dev/null || (Xvfb :99 -screen 0 1600x1000x24 -nolisten tcp >/dev/null 2>&1 &)
mkdir -p $R/src/fwc
rsync -a --delete --exclude target /home/claude/folio-writer/core/ $R/src/fwc/
if [ "$1" = build ]; then
  chroot $R bash -c ". /root/cargoenv.sh; cd /src/fwc && ./build-jammy.sh 2>&1 | grep -E '^error|Finished' -A7 | tail -20"
fi
rm -rf $R/tmp/fw; mkdir -p $R/tmp/fw
cp -r /home/claude/folio-writer/app /home/claude/folio-writer/share /home/claude/folio-writer/tests $R/tmp/fw/
cp $R/src/fwc/target/release/libfolio_core.so $R/tmp/fw/app/folio_core.so
