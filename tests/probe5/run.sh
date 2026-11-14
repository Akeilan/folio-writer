#!/bin/bash
# run.sh <probe.py> [display] : run one probe inside Page (source tree) on the 22.04 machine
P=$1; D=${2:-98}; N=$(basename $P .py)
R=/srv/jammy
pgrep -f "^Xvfb :$D " >/dev/null || { rm -f /tmp/.X$D-lock; setsid -f Xvfb :$D -screen 0 1600x1000x24 -nolisten tcp </dev/null >/dev/null 2>&1; sleep 1; }
mkdir -p $R/tmp/p5
rsync -a --delete /home/claude/folio-writer/app /home/claude/folio-writer/share /home/claude/folio-writer/tests $R/tmp/p5/
cp $R/src/fwc/target/release/libfolio_core.so $R/tmp/p5/app/folio_core.so
sed -i "s#/tmp/ftest.log#/tmp/p5log_$N.log#; s#/tmp/fshot_#/tmp/p5shot_#" $R/tmp/p5/tests/common.py
mkdir -p $R/tmp/p5/probes $R/tmp/p5out; cp /home/claude/p5/*.py $R/tmp/p5/probes/ 2>/dev/null
rm -f $R/tmp/p5log_$N.log; H=${HOMEN:-$N}; [ -n "$KEEPHOME" ] || rm -rf $R/tmp/p5home_$H; mkdir -p $R/tmp/p5home_$H
chroot $R bash -c "cd /tmp/p5; HOME=/tmp/p5home_$H XDG_CONFIG_HOME=/tmp/p5home_$H/.config DISPLAY=:$D FOLIO_ENGINE=native FOLIO_SHARE=/tmp/p5/share FOLIO_WRITER_TESTS=/tmp/p5/tests FOLIO_TEST_SCRIPT=/tmp/p5/probes/$N.py PATH=${EXTRAPATH:+$EXTRAPATH:}$PATH PYTHONPATH=app timeout ${T:-600} python3 -m folio > /tmp/p5out/$N.out 2>&1; echo rc=\$?"
echo "pass=$(grep -c ^PASS $R/tmp/p5log_$N.log 2>/dev/null) fail=$(grep -c ^FAIL $R/tmp/p5log_$N.log 2>/dev/null) err=$(grep -c ^ERROR $R/tmp/p5log_$N.log 2>/dev/null)"
