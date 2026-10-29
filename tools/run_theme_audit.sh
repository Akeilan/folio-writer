#!/bin/bash
# X2-01: Writer under a dark desktop theme and a loud coloured one (inside the build root, or
# with APP=installed for the installed package). Prints one summary line per theme.
cd /tmp/fw 2>/dev/null || true
rc=0
for t in dark colour; do
  TH=$(python3 tests/themecheck.py $t)
  if [ "$APP" = installed ]; then
    DISPLAY=:99 GTK_THEME=$TH FOLIO_ENGINE=native FOLIO_TEST_SCRIPT=$PWD/tests/theme_audit.py UI_OUT=/tmp/theme_$t timeout 900 folio-writer >/tmp/theme_$t.out 2>&1
  else
    DISPLAY=:99 GTK_THEME=$TH FOLIO_ENGINE=native FOLIO_SHARE=/tmp/fw/share FOLIO_TEST_SCRIPT=/tmp/fw/tests/theme_audit.py UI_OUT=/tmp/theme_$t PYTHONPATH=app timeout 900 ${PYRUN:-python3} -m folio >/tmp/theme_$t.out 2>&1
  fi
  r=$?
  echo "theme $t rc=$r $(grep -c '^FAIL' /tmp/theme_$t.out) problems; $(grep 'checked:' /tmp/theme_$t.out)"
  [ $r = 0 ] || rc=1
done
exit $rc
