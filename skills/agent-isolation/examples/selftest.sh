#!/bin/sh
# Self-test for agent-isolation: the checker passes a split-session layout and
# catches the trifecta, the ungated irreversible action, the forbidden identity,
# and the unclassified capability.
cd "$(dirname "$0")" || exit 2
C=../scripts/trifecta_check.py
fail=0

python3 "$C" --manifest sessions.good.json >/dev/null 2>&1
[ $? -eq 0 ] && echo "PASS  split sessions -> exit 0" || { echo "FAIL  good manifest"; fail=1; }

out=$(python3 "$C" --manifest sessions.bad.json 2>&1); code=$?
[ $code -eq 1 ] && echo "PASS  unsafe manifest -> exit 1" || { echo "FAIL  bad manifest (got $code)"; fail=1; }
echo "$out" | grep -q "LETHAL TRIFECTA" && echo "PASS  trifecta caught" || { echo "FAIL  trifecta"; fail=1; }
echo "$out" | grep -q "without approval_required:true" && echo "PASS  ungated irreversible caught" || { echo "FAIL  approval"; fail=1; }
echo "$out" | grep -q "forbidden identity" && echo "PASS  forbidden identity caught" || { echo "FAIL  identity"; fail=1; }
echo "$out" | grep -q "unclassified" && echo "PASS  unclassified capability caught" || { echo "FAIL  classify"; fail=1; }

python3 "$C" --manifest no-such.json >/dev/null 2>&1
[ $? -eq 2 ] && echo "PASS  missing manifest -> exit 2" || { echo "FAIL  input error"; fail=1; }

[ $fail -eq 0 ] && echo "SELFTEST OK" || echo "SELFTEST FAILED"
exit $fail
