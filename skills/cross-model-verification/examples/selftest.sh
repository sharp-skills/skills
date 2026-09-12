#!/bin/sh
# Self-test for cross-model-verification: floor, wiring, fail-soft.
cd "$(dirname "$0")" || exit 2
V=../scripts/verify_handoff.py
fail=0

python3 "$V" handoff.good.json --spec handoff-spec.json >/dev/null 2>&1
[ $? -eq 0 ] && echo "PASS  complete hand-off -> exit 0" || { echo "FAIL  good"; fail=1; }

out=$(python3 "$V" handoff.bad.json --spec handoff-spec.json 2>&1); code=$?
[ $code -eq 1 ] && echo "PASS  broken hand-off -> exit 1" || { echo "FAIL  bad (got $code)"; fail=1; }
echo "$out" | grep -q "acceptance_criteria' is empty" && echo "PASS  empty required field caught" || { echo "FAIL  empty field"; fail=1; }
echo "$out" | grep -q "appears in both" && echo "PASS  no-touch/modify contradiction caught" || { echo "FAIL  contradiction"; fail=1; }

out=$(python3 "$V" handoff.good.json --spec handoff-spec.json --upstream blueprint.json --verifier-cmd "python3 fake_verifier.py" 2>&1); code=$?
[ $code -eq 1 ] && echo "$out" | grep -q "cross-model" && echo "PASS  cross-model verifier wired, its gap surfaces -> exit 1" || { echo "FAIL  verifier wiring (got $code)"; fail=1; }

out=$(python3 "$V" handoff.good.json --spec handoff-spec.json --upstream blueprint.json --verifier-cmd "/nonexistent-model-cli" 2>&1); code=$?
[ $code -eq 0 ] && echo "$out" | grep -q "control arm" && echo "PASS  dead verifier fails SOFT -> exit 0 with note" || { echo "FAIL  fail-soft (got $code)"; fail=1; }

python3 "$V" no-such.json --spec handoff-spec.json >/dev/null 2>&1
[ $? -eq 2 ] && echo "PASS  missing input fails loudly -> exit 2" || { echo "FAIL  input error"; fail=1; }

[ $fail -eq 0 ] && echo "SELFTEST OK" || echo "SELFTEST FAILED"
exit $fail
