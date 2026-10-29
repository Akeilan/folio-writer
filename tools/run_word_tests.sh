#!/bin/bash
# inside the build root: the Word-parity scenarios (tests/word), against Folio's own engine.
# Builds their sample files first; prints one line per script and the failures.
# APP=installed: against the installed package (folio-page on PATH) instead of /tmp/fw/app
cd /tmp/fw
if [ "$APP" = installed ]; then
  export FOLIO_APP_DIR=/usr/lib/folio-page FOLIO_TEMPLATES=/usr/share/folio-page/templates
else
  export FOLIO_APP_DIR=/tmp/fw/app FOLIO_TEMPLATES=/tmp/fw/share/templates
fi
PYTHONPATH=$FOLIO_APP_DIR python3 tests/word/helpers/make_fixtures.py >/tmp/fixtures.log 2>&1 || cat /tmp/fixtures.log
rm -f /tmp/wc_results.txt /tmp/word_fail.txt
for f in ${@:-tests/word/[cdlrwx]*.py}; do
  case $f in */wc.py|*/wn.py) continue;; esac
  rm -f /tmp/ftest.log
  if [ "$APP" = installed ]; then
    DISPLAY=${DISPLAY:-:99} FOLIO_ENGINE=native FOLIO_TEST_SCRIPT=/tmp/fw/$f timeout 300 folio-page >/tmp/$(basename $f).out 2>&1
  else
    DISPLAY=${DISPLAY:-:99} FOLIO_ENGINE=native FOLIO_SHARE=/tmp/fw/share FOLIO_TEST_SCRIPT=/tmp/fw/$f PYTHONPATH=app${EXTRA_PYTHONPATH:+:$EXTRA_PYTHONPATH} timeout 300 ${PYRUN:-python3} -m folio >/tmp/$(basename $f).out 2>&1
  fi
  echo "$(basename $f) rc=$? pass=$(grep -c ^PASS /tmp/ftest.log) fail=$(grep -c ^FAIL /tmp/ftest.log) err=$(grep -c '^ERROR' /tmp/ftest.log) done=$(grep -c ALLDONE /tmp/ftest.log)"
  grep "^FAIL\|^ERROR" /tmp/ftest.log | sed "s#^#$(basename $f): #" >> /tmp/word_fail.txt
done
echo "--- failures"
cat /tmp/word_fail.txt
