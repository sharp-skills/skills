#!/bin/sh
# Self-test for prompt-contracts: proves the checker catches what it claims to.
# Expected: clean config exits 0, planted violations exit 1, broken wiring exits 2.
cd "$(dirname "$0")" || exit 2
CHECK=../scripts/contract_check.py
fail=0

python3 "$CHECK" --config config.clean.json >/dev/null 2>&1
[ $? -eq 0 ] && echo "PASS  clean contract -> exit 0" || { echo "FAIL  clean contract"; fail=1; }

python3 "$CHECK" --config config.broken.json >/dev/null 2>&1
[ $? -eq 1 ] && echo "PASS  oneOf-hidden enum + stale prompt example -> exit 1" || { echo "FAIL  violations not caught"; fail=1; }

python3 "$CHECK" --config config.badwiring.json >/dev/null 2>&1
[ $? -eq 2 ] && echo "PASS  empty glob fails loudly -> exit 2" || { echo "FAIL  wiring error not loud"; fail=1; }

# --- versioning: a prompt is a released artifact (fixtures under versioning/) ---
V=../scripts/prompt_version_check.py
python3 "$V" --manifest versioning/prompts.good.json >/dev/null 2>&1
[ $? -eq 0 ] && echo "PASS  well-versioned manifest -> exit 0" || { echo "FAIL  good manifest"; fail=1; }

out=$(python3 "$V" --manifest versioning/prompts.bad.json 2>&1); code=$?
[ $code -eq 1 ] && echo "PASS  broken manifest -> exit 1" || { echo "FAIL  bad manifest (got $code)"; fail=1; }
echo "$out" | grep -q "edited without a version bump" && echo "PASS  edit-in-place drift caught" || { echo "FAIL  pin drift"; fail=1; }
echo "$out" | grep -q "planner:v2: empty changelog" && echo "PASS  empty changelog caught" || { echo "FAIL  changelog"; fail=1; }
echo "$out" | grep -q "rollback_to 'v9'" && echo "PASS  dangling rollback caught" || { echo "FAIL  rollback"; fail=1; }
echo "$out" | grep -q "active version 'v5' is not in" && echo "PASS  missing active caught" || { echo "FAIL  active"; fail=1; }

python3 "$V" --manifest versioning/no-such.json >/dev/null 2>&1
[ $? -eq 2 ] && echo "PASS  missing manifest -> exit 2" || { echo "FAIL  versioning input error"; fail=1; }

[ $fail -eq 0 ] && echo "SELFTEST OK" || echo "SELFTEST FAILED"
exit $fail
