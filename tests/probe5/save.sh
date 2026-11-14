#!/bin/bash
cd /home/claude/folio-writer && cp /home/claude/p5/*.py /home/claude/p5/*.sh /home/claude/p5/findings.md tests/probe5/ && cp /srv/jammy/tmp/p5out/*.tsv tests/probe5/ 2>/dev/null; git add -A && git -c user.name=Claude -c user.email=noreply@anthropic.com commit -q -m "Backlog 5 probes: ${1:-progress}

Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01L7oDhePMuTSzKAPokorihB" && git push -q origin backlog5 2>&1 | grep -v "^remote:" ; git log --oneline -1 | cat
