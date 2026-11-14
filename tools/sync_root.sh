#!/bin/bash
# Copy the tree into a build root of its own: sync_root.sh <name>  (e.g. gate, probe).
# Each run gets its own root so one run can never overwrite the files another is using.
set -e
W=/home/claude/folio-writer
R=/srv/jammy
N=${1:?a name for the root}
D=$R/tmp/fw-$N
rm -rf "$D"; mkdir -p "$D"
cp -r $W/app $W/share $W/tests $W/tools "$D/"
cp $R/src/fwc/target/release/libfolio_core.so "$D/app/folio_core.so"
mkdir -p "$D/probes"; cp /home/claude/p5/*.py "$D/probes/" 2>/dev/null || true
sed -i "s#/tmp/p5/probes/#/tmp/fw-$N/probes/#g; s#/tmp/fw/probes/#/tmp/fw-$N/probes/#g" "$D"/probes/*.py 2>/dev/null || true
echo "/tmp/fw-$N"
