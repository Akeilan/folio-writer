#!/bin/bash
# inside the build root: every native-engine UI test; prints one line per script
# FW: the build root to test, so two runs on one machine never share files
FW=${FW:-/tmp/fw}
cd "$FW"
rm -f /tmp/wc_results.txt ${FOLIO_TEST_LOG:-/tmp/ftest.log}
for f in ${@:-tests/native/n*.py}; do
  rm -f ${FOLIO_TEST_LOG:-/tmp/ftest.log}
  DISPLAY=${DISPLAY:-:99} FOLIO_TEST_LOG=${FOLIO_TEST_LOG:-/tmp/ftest.log} FOLIO_ENGINE=native FOLIO_SHARE="$FW"/share FOLIO_TEST_SCRIPT="$FW"/$f PYTHONPATH=app${EXTRA_PYTHONPATH:+:$EXTRA_PYTHONPATH} timeout 300 ${PYRUN:-python3} -m folio >/tmp/$(basename $f).out 2>&1
  echo "$(basename $f) rc=$? pass=$(grep -c ^PASS ${FOLIO_TEST_LOG:-/tmp/ftest.log}) fail=$(grep -c ^FAIL ${FOLIO_TEST_LOG:-/tmp/ftest.log}) err=$(grep -c '^ERROR' ${FOLIO_TEST_LOG:-/tmp/ftest.log})"
  grep "^FAIL\|^ERROR" ${FOLIO_TEST_LOG:-/tmp/ftest.log} | head -10 | sed "s#^#  $(basename $f): #"
done
