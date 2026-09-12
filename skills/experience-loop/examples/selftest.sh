#!/bin/sh
# Self-test for experience-loop: EMA math, structured entries, staleness.
cd "$(dirname "$0")" || exit 2
L=../scripts/learnings.py
F=/tmp/exp-loop-selftest.json
rm -f "$F"
fail=0

# EMA: bootstrap 70, record 90 -> 0.3*90+0.7*70 = 76.0
out=$(python3 "$L" record --file "$F" --agent analyst --confidence 90 2>&1)
echo "$out" | grep -q "70.0 -> 76.0" && echo "PASS  EMA math exact (70 -> 76.0 on obs 90)" || { echo "FAIL  EMA: $out"; fail=1; }

# second observation 50 -> 0.3*50+0.7*76 = 68.2
out=$(python3 "$L" record --file "$F" --agent analyst --confidence 50 \
      --category schema_drift --insight "enum drifted" --outcome "aligned + CI check" 2>&1)
echo "$out" | grep -q "76.0 -> 68.2" && echo "PASS  EMA folds second observation (-> 68.2)" || { echo "FAIL  EMA2: $out"; fail=1; }

python3 "$L" show analyst --file "$F" 2>/dev/null | grep -q "schema_drift" \
  && echo "PASS  structured learning recorded and shown" || { echo "FAIL  show"; fail=1; }

# incomplete learning refused
python3 "$L" record --file "$F" --agent analyst --confidence 80 --category x >/dev/null 2>&1
[ $? -eq 2 ] && echo "PASS  unstructured entry refused -> exit 2" || { echo "FAIL  structure guard"; fail=1; }

# staleness: fresh now; stale with max-age 0
python3 "$L" check-staleness --file "$F" --max-age-days 14 >/dev/null 2>&1
[ $? -eq 0 ] && echo "PASS  fresh file -> exit 0" || { echo "FAIL  fresh"; fail=1; }
sleep 1
python3 "$L" check-staleness --file "$F" --max-age-days 0.00001 >/dev/null 2>&1
[ $? -eq 1 ] && echo "PASS  stale file caught -> exit 1" || { echo "FAIL  stale"; fail=1; }

rm -f "$F"

# red fixture: learnings.stale.json — a plausible store (real EMA values,
# structured entries) whose last write is months old.
# fails because: capture-at-completion bug — the recorder was hooked to an
# approval gate instead of run completion, so the loop silently stopped
# writing and every later agent bootstraps on stale experience.
out=$(python3 "$L" check-staleness --file learnings.stale.json --max-age-days 14 2>&1); code=$?
[ $code -eq 1 ] && echo "PASS  shipped stale store caught -> exit 1" \
  || { echo "FAIL  stale store (got $code)"; fail=1; }
echo "$out" | grep -q "STALE" && echo "PASS  staleness message names the failure" \
  || { echo "FAIL  stale message"; fail=1; }

[ $fail -eq 0 ] && echo "SELFTEST OK" || echo "SELFTEST FAILED"
exit $fail
