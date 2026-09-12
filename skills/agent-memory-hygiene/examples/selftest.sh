#!/bin/sh
# Self-test for agent-memory-hygiene: healthy store passes; each rot is caught.
cd "$(dirname "$0")" || exit 2
L=../scripts/memory_lint.py
NOW=2026-07-06T00:00:00Z
fail=0

python3 "$L" --store store.good.json --now "$NOW" >/dev/null 2>&1
[ $? -eq 0 ] && echo "PASS  healthy store -> exit 0" || { echo "FAIL  good store"; fail=1; }

out=$(python3 "$L" --store store.bad.json --now "$NOW" 2>&1); code=$?
[ $code -eq 1 ] && echo "PASS  rotten store -> exit 1" || { echo "FAIL  bad store (got $code)"; fail=1; }
echo "$out" | grep -q "API key" && echo "PASS  secret caught" || { echo "FAIL  secret"; fail=1; }
echo "$out" | grep -q "b2: no 'source'" && echo "PASS  missing provenance caught" || { echo "FAIL  provenance"; fail=1; }
echo "$out" | grep -q "b3:.*un-reviewed" && echo "PASS  stale entry caught" || { echo "FAIL  staleness"; fail=1; }
echo "$out" | grep -q "b4:.*authoritative fact" && echo "PASS  poison (untrusted-as-fact) caught" || { echo "FAIL  poison"; fail=1; }
echo "$out" | grep -q "b5: duplicate" && echo "PASS  duplicate caught" || { echo "FAIL  duplicate"; fail=1; }

# size cap
out=$(python3 "$L" --store store.good.json --now "$NOW" --max-entries 2 2>&1); code=$?
[ $code -eq 1 ] && echo "PASS  size cap -> exit 1" || { echo "FAIL  size cap (got $code)"; fail=1; }
echo "$out" | grep -q "drowns recall" && echo "PASS  unbounded growth caught" || { echo "FAIL  growth"; fail=1; }

python3 "$L" --store no-such.json --now "$NOW" >/dev/null 2>&1
[ $? -eq 2 ] && echo "PASS  missing store -> exit 2" || { echo "FAIL  input error"; fail=1; }

[ $fail -eq 0 ] && echo "SELFTEST OK" || echo "SELFTEST FAILED"
exit $fail
