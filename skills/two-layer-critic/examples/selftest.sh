#!/bin/sh
# Self-test for two-layer-critic: tier routing + review-output policy.
cd "$(dirname "$0")" || exit 2
C=../scripts/critic_policy.py
fail=0

out=$(python3 "$C" route --mode STANDARD --policy critic-policy.json 2>&1)
[ "$out" = "cheap" ] && echo "PASS  STANDARD -> cheap tier" || { echo "FAIL  route standard: $out"; fail=1; }
out=$(python3 "$C" route --mode DEEP --policy critic-policy.json 2>&1)
[ "$out" = "premium" ] && echo "PASS  DEEP -> premium tier (reserved)" || { echo "FAIL  route deep: $out"; fail=1; }
python3 "$C" route --mode FAST --policy critic-policy.json 2>/dev/null | grep -q "skip" \
  && echo "PASS  FAST -> review skipped" || { echo "FAIL  route fast"; fail=1; }
python3 "$C" route --mode BOGUS --policy critic-policy.json >/dev/null 2>&1
[ $? -eq 2 ] && echo "PASS  unknown mode fails loudly -> exit 2" || { echo "FAIL  unknown mode"; fail=1; }

python3 "$C" validate review.good.json --policy critic-policy.json >/dev/null 2>&1
[ $? -eq 0 ] && echo "PASS  structured capped review -> exit 0" || { echo "FAIL  good review"; fail=1; }

out=$(python3 "$C" validate review.bad.json --policy critic-policy.json 2>&1); code=$?
[ $code -eq 1 ] && echo "PASS  bad review -> exit 1" || { echo "FAIL  bad review (got $code)"; fail=1; }
echo "$out" | grep -q "4 findings > cap 3" && echo "PASS  finding cap enforced" || { echo "FAIL  cap"; fail=1; }
echo "$out" | grep -q "verdict 'SCORE_74'" && echo "PASS  score-creep verdict rejected" || { echo "FAIL  verdict"; fail=1; }
echo "$out" | grep -q "missing/empty 'fix_direction'" && echo "PASS  unstructured finding rejected" || { echo "FAIL  structure"; fail=1; }
echo "$out" | grep -q "severity 'NIT'" && echo "PASS  unknown severity rejected" || { echo "FAIL  severity"; fail=1; }

[ $fail -eq 0 ] && echo "SELFTEST OK" || echo "SELFTEST FAILED"
exit $fail
