#!/bin/bash
# Folio Page (formerly Folio Writer): source tests (native UI, Word parity, command walk, themes),
# the two debs (folio-page + transitional folio-writer), then on jammy, nolo and noble IN PARALLEL
# (displays :99, :93, :92): the upgrade from the last folio-writer, and the installed tests
# (native UI, Word parity, themes); noble adds the Wayland pass. One summary per machine at the end.
set -u
W=/home/claude/folio-writer
LOGS=${LOGS:-/home/claude/out/page_release_logs}; mkdir -p $LOGS
PREV=${PREV:-/home/claude/out/folio-writer_2.32.0_amd64.deb}
/home/claude/mounts.sh
for d in 99 93 92; do pgrep -f "^Xvfb :$d " >/dev/null || { rm -f /tmp/.X$d-lock /tmp/.X11-unix/X$d; setsid -f Xvfb :$d -screen 0 1600x1000x24 -nolisten tcp </dev/null >/dev/null 2>&1; }; done
sleep 1
quiet() {  # keep lines that aren't a clean result; count the clean ones
  awk '/ rc=0 pass=[1-9][0-9]* fail=0 err=0( done=1)?$/ || / rc=0 pass=0 fail=0 err=0 done=1$/ || /^theme [a-z]+ rc=0 0 problems/ {ok++; next} / rc=/ {bad++} {print} END {printf "  (%d clean, %d not)\n", ok, bad}'
}
# the engine is built on 22.04 (its glibc), never on the host
bash $W/tools/sync_chroot.sh build || exit 1
mkdir -p $W/core/target/release; cp /srv/jammy/src/fwc/target/release/libfolio_core.so $W/core/target/release/libfolio_core.so
if [ -z "${SKIP_SOURCE:-}" ]; then
bash $W/tools/sync_chroot.sh; cp -r $W/tools /srv/jammy/tmp/fw/; mkdir -p /srv/jammy/home/claude; ln -sfn /tmp/fw /srv/jammy/home/claude/folio2
echo "== native (source)"; chroot /srv/jammy bash -c "DISPLAY=:99 bash /tmp/fw/tools/run_native_tests.sh" 2>&1 | quiet
echo "== word parity (source)"; chroot /srv/jammy bash -c "DISPLAY=:99 bash /tmp/fw/tools/run_word_tests.sh" 2>&1 | quiet
echo "== command walk"
chroot /srv/jammy bash -c "cd /tmp/fw; DISPLAY=:99 FOLIO_ENGINE=native FOLIO_SHARE=/tmp/fw/share FOLIO_TEST_SCRIPT=/tmp/fw/tests/native_command_walk.py PYTHONPATH=app timeout 1500 python3 -m folio > /tmp/walk.out 2>&1; echo \"walk rc=\$? done=\$(grep -c '^DONE' /tmp/walk.out) tracebacks=\$(grep -c Traceback /tmp/walk.out)\""
echo "== rename (X3-08)"; chroot /srv/jammy bash -c "cd /tmp/fw; PYTHONPATH=app python3 tests/rename_test.py | tail -1"
echo "== themes (source)"; chroot /srv/jammy bash -c "DISPLAY=:99 bash /tmp/fw/tools/run_theme_audit.sh"
fi
echo "== debs"
NO_CORE=1 bash $W/build-deb.sh /home/claude/out > $LOGS/build.log 2>&1
NEW=$(grep "folio-page_.*\.deb$" $LOGS/build.log | tail -1); TRANS=$(grep "folio-writer_.*_all\.deb$" $LOGS/build.log | tail -1)
for f in "$NEW" "$TRANS"; do [ -f "$f" ] || { echo "build failed"; tail -20 $LOGS/build.log; exit 1; }; cp -f "$f" /home/claude/out/ 2>/dev/null; done
NEW=/home/claude/out/$(basename $NEW); TRANS=/home/claude/out/$(basename $TRANS); ls -la $NEW $TRANS
machine() {  # root display
  local m=$1 d=$2 log=$LOGS/$(basename $1).log
  {
    mountpoint -q $m/dev/pts || mount -t devpts devpts $m/dev/pts 2>/dev/null
    cp $NEW $TRANS $PREV $m/tmp/
    echo "-- upgrade from $(basename $PREV)"
    flock /home/claude/.dpkg.lock chroot $m bash -c "export DEBIAN_FRONTEND=noninteractive
      dpkg --purge --force-depends folio-page folio-writer >/dev/null 2>&1
      dpkg -i /tmp/$(basename $PREV) >/dev/null 2>&1 || apt-get -y -f install >/dev/null 2>&1
      echo \"before: \$(dpkg-query -W -f='\${Package} \${Version}' folio-writer 2>/dev/null)\"
      cd /tmp && apt-get install -y ./$(basename $NEW) ./$(basename $TRANS) >/tmp/up.log 2>&1 || { echo 'UPGRADE FAILED'; tail -5 /tmp/up.log; }
      dpkg -l folio-page folio-writer | grep '^ii' | awk '{print \$1,\$2,\$3}'
      echo \"folio-page: \$(folio-page --version)\"; echo \"folio-writer: \$(folio-writer --version)\"
      ls /usr/share/applications/folio-page.desktop /usr/share/applications/folio-writer.desktop >/dev/null && echo 'desktop ids: both'
      [ -d /usr/lib/folio-writer ] && echo 'OLD /usr/lib/folio-writer still there' || echo 'old install dir gone'"
    rm -rf $m/tmp/fw; mkdir -p $m/tmp/fw; cp -r $W/tests $W/tools $m/tmp/fw/
    mkdir -p $m/home/claude; ln -sfn /tmp/fw $m/home/claude/folio2
    echo "-- installed tests"
    chroot $m bash -c "DISPLAY=:$d bash /tmp/fw/tools/run_installed_tests.sh" 2>&1 | grep -v "^--- failures$" | quiet
    if [ "$(basename $m)" = noble ]; then
      cp /home/claude/folio-suite/tests/wl.sh $m/tmp/wl.sh; chmod +x $m/tmp/wl.sh
      echo "-- Wayland"
      chroot $m bash -c "export DISPLAY=:$d; APP=installed /tmp/wl.sh bash /tmp/fw/tools/run_theme_audit.sh"
      chroot $m bash -c "export DISPLAY=:$d XTEST_DISPLAY=:$d; TESTS='tests/native/n1.py tests/native/n31.py tests/native/n37.py' /tmp/wl.sh bash /tmp/fw/tools/run_installed_tests.sh" 2>&1 | quiet
    fi
  } > $log 2>&1
}
machine /srv/jammy 99 & machine /srv/nolo 93 & machine /srv/noble 92 &
wait
for m in jammy nolo noble; do echo "== $m"; cat $LOGS/$m.log; done
