#!/bin/bash
# inside the build root: the Word-parity scenarios (tests/word), against Folio's own engine.
# Builds their sample files first; prints one line per script and the failures.
cd /tmp/fw
PYTHONPATH=/tmp/fw/app python3 tests/word/helpers/make_fixtures.py >/tmp/fixtures.log 2>&1 || cat /tmp/fixtures.log
rm -f /tmp/wc_results.txt /tmp/word_fail.txt
for f in ${@:-tests/word/[cdlrwx]*.py}; do
  case $f in */wc.py|*/wn.py) continue;; esac
  rm -f /tmp/ftest.log
  DISPLAY=${DISPLAY:-:99} FOLIO_ENGINE=native FOLIO_SHARE=/tmp/fw/share FOLIO_TEST_SCRIPT=/tmp/fw/$f PYTHONPATH=app${EXTRA_PYTHONPATH:+:$EXTRA_PYTHONPATH} timeout 300 python3 -m folio >/tmp/$(basename $f).out 2>&1
  echo "$(basename $f) rc=$? pass=$(grep -c ^PASS /tmp/ftest.log) fail=$(grep -c ^FAIL /tmp/ftest.log) err=$(grep -c '^ERROR' /tmp/ftest.log) done=$(grep -c ALLDONE /tmp/ftest.log)"
  grep "^FAIL\|^ERROR" /tmp/ftest.log | sed "s#^#$(basename $f): #" >> /tmp/word_fail.txt
done
echo "--- failures"
cat /tmp/word_fail.txt
