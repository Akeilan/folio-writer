#!/bin/bash
# inside the build root: every native-engine UI test; prints one line per script
cd /tmp/fw
rm -f /tmp/wc_results.txt /tmp/ftest.log
for f in ${@:-tests/native/n*.py}; do
  rm -f /tmp/ftest.log
  DISPLAY=${DISPLAY:-:99} FOLIO_ENGINE=native FOLIO_SHARE=/tmp/fw/share FOLIO_TEST_SCRIPT=/tmp/fw/$f PYTHONPATH=app${EXTRA_PYTHONPATH:+:$EXTRA_PYTHONPATH} timeout 300 ${PYRUN:-python3} -m folio >/tmp/$(basename $f).out 2>&1
  echo "$(basename $f) rc=$? pass=$(grep -c ^PASS /tmp/ftest.log) fail=$(grep -c ^FAIL /tmp/ftest.log) err=$(grep -c '^ERROR' /tmp/ftest.log)"
  grep "^FAIL\|^ERROR" /tmp/ftest.log | head -10 | sed "s#^#  $(basename $f): #"
done
