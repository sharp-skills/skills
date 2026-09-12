#!/bin/sh
# Self-test for earned-autonomy: the checker passes a defensible grant ledger, and
# catches each way an agent ends up holding authority nobody deliberately gave it.
cd "$(dirname "$0")" || exit 2
C=../scripts/autonomy_check.py
fail=0

# a ledger where every rung is paid for -> 0
python3 "$C" --grants grants.good.jsonl >/dev/null 2>&1
[ $? -eq 0 ] && echo "PASS  defensible ledger -> exit 0" || { echo "FAIL  clean case"; fail=1; }

python3 "$C" --grants grants.good.jsonl --strict >/dev/null 2>&1
[ $? -eq 0 ] && echo "PASS  defensible ledger --strict -> exit 0" || { echo "FAIL  clean strict case"; fail=1; }

# the sick ledger -> 1, with every failure mode named
out=$(python3 "$C" --grants grants.bad.jsonl 2>&1); code=$?
[ $code -eq 1 ] && echo "PASS  ungoverned ledger -> exit 1" || { echo "FAIL  ungoverned ledger (got $code)"; fail=1; }

echo "$out" | grep -q "authority must be conferred by a human" \
  && echo "PASS  self-granted authority caught (the core invariant)" || { echo "FAIL  self-grant check"; fail=1; }
echo "$out" | grep -q "trailing clean streak of 3" \
  && echo "PASS  unearned promotion caught" || { echo "FAIL  streak check"; fail=1; }
echo "$out" | grep -q "earned somewhere else" \
  && echo "PASS  borrowed track record caught" || { echo "FAIL  evidence-scope check"; fail=1; }
echo "$out" | grep -q "grants key on" \
  && echo "PASS  wildcard resource caught" || { echo "FAIL  scope check"; fail=1; }
echo "$out" | grep -q "produces a proposal" \
  && echo "PASS  proposal rung that actually acts caught" || { echo "FAIL  side-effect check"; fail=1; }
echo "$out" | grep -q "unwatched channel" \
  && echo "PASS  approval routed into an unread channel caught" || { echo "FAIL  watched-channel check"; fail=1; }

# the streak must be TRAILING: one edit at the end resets it
printf '%s\n' '{"grant_id":"t1","action":"a","resource":"r","principal":"agent:x","rung":"act","granted_by":"human:y","evidence":{"scope":"a@r","verdicts":["accepted","accepted","accepted","accepted","accepted","accepted","accepted","accepted","accepted","accepted","accepted","edited"]}}' > .streak.jsonl
python3 "$C" --grants .streak.jsonl 2>&1 | grep -q "trailing clean streak of 0" \
  && echo "PASS  one edit resets the streak (trailing, not total)" || { echo "FAIL  trailing-streak semantics"; fail=1; }
rm -f .streak.jsonl

# a low rung is not asked to prove anything
echo "$out" | grep -q "g-wildcard: rung" && { echo "FAIL  propose rung asked for a streak"; fail=1; } \
  || echo "PASS  low rungs need no track record"

# --strict adds the expiry check and nothing else
n=$(python3 "$C" --grants grants.bad.jsonl --quiet 2>&1 | grep -o '[0-9]* violation' | cut -d' ' -f1)
s=$(python3 "$C" --grants grants.bad.jsonl --strict --quiet 2>&1 | grep -o '[0-9]* violation' | cut -d' ' -f1)
[ "$s" -eq $((n + 1)) ] && echo "PASS  --strict adds exactly the expiry check ($n -> $s)" \
  || { echo "FAIL  strict delta ($n -> $s)"; fail=1; }

python3 "$C" --grants grants.bad.jsonl --strict 2>&1 | grep -q "never revisited" \
  && echo "PASS  never-expiring grant caught under --strict" || { echo "FAIL  expiry check"; fail=1; }

# threshold is configurable, and raising it must bite
python3 "$C" --grants grants.good.jsonl --min-streak 20 2>&1 | grep -q "needs 20" \
  && echo "PASS  --min-streak raises the bar on an already-clean ledger" || { echo "FAIL  min-streak"; fail=1; }

# bad input must fail loud, not pass quietly
python3 "$C" --grants no-such-file.jsonl >/dev/null 2>&1
[ $? -eq 2 ] && echo "PASS  missing ledger -> exit 2 (fail loud)" || { echo "FAIL  missing-file handling"; fail=1; }

printf '# comment only\n' > .empty.jsonl
python3 "$C" --grants .empty.jsonl >/dev/null 2>&1
[ $? -eq 2 ] && echo "PASS  empty ledger -> exit 2 (cannot pass by governing nothing)" \
  || { echo "FAIL  empty-ledger handling"; fail=1; }
rm -f .empty.jsonl

printf '{"grant_id":"u1","action":"a","resource":"r","principal":"p","rung":"act","granted_by":"human:y","evidence":{"verdicts":["approved"]}}\n' > .verdict.jsonl
python3 "$C" --grants .verdict.jsonl >/dev/null 2>&1
[ $? -eq 2 ] && echo "PASS  unknown verdict -> exit 2 (typo must not read as clean)" \
  || { echo "FAIL  verdict validation"; fail=1; }
rm -f .verdict.jsonl

printf 'not json\n' > .broken.jsonl
python3 "$C" --grants .broken.jsonl >/dev/null 2>&1
[ $? -eq 2 ] && echo "PASS  malformed ledger -> exit 2" || { echo "FAIL  malformed handling"; fail=1; }
rm -f .broken.jsonl

[ $fail -eq 0 ] && echo "ALL PASS" || echo "FAILURES"
exit $fail
