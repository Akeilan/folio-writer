#!/bin/bash
# The installed package (folio-writer on PATH) under the native UI tests, the Word-parity
# scenarios and the theme audit. Run inside a root that has the .deb installed and this
# tests/ tree at /tmp/fw/tests (with /home/claude/folio2 -> /tmp/fw).
cd /tmp/fw
D=${DISPLAY:-:99}
run() {
  rm -f /tmp/ftest.log
  DISPLAY=$D FOLIO_ENGINE=native FOLIO_TEST_SCRIPT=/tmp/fw/$1 timeout 300 folio-writer >/tmp/inst_$(basename $1).out 2>&1
  echo "$(basename $1) rc=$? pass=$(grep -c ^PASS /tmp/ftest.log) fail=$(grep -c ^FAIL /tmp/ftest.log) err=$(grep -c '^ERROR' /tmp/ftest.log)"
  grep "^FAIL\|^ERROR" /tmp/ftest.log | sed "s#^#  $(basename $1): #"
}
echo "folio-writer $(python3 -c 'import sys; sys.path.insert(0, "/usr/lib/folio-writer"); import folio; print(folio.VERSION)')"
for f in ${TESTS:-tests/native/n*.py}; do run $f; done
if [ -z "$TESTS" ]; then
  python3 -c 'import sys; sys.path.insert(0, "/usr/lib/folio-writer"); import folio_core' && echo "engine loads"
  APP=installed DISPLAY=$D bash /tmp/fw/tools/run_theme_audit.sh
fi
