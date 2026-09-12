#!/bin/sh
# Self-test for cost-budgeting: healthy pass, named overruns, coverage gap.
cd "$(dirname "$0")" || exit 2
C=../scripts/budget_check.py
fail=0

python3 "$C" --traces-dir traces demo-run-001 --budgets budgets.json >/dev/null 2>&1
[ $? -eq 0 ] && echo "PASS  healthy trace within budget -> exit 0" || { echo "FAIL  healthy"; fail=1; }

out=$(python3 "$C" --traces-dir traces over-budget-run --budgets budgets.json 2>&1); code=$?
[ $code -eq 1 ] && echo "PASS  over-budget trace -> exit 1" || { echo "FAIL  overrun (got $code)"; fail=1; }
echo "$out" | grep -q "engineer: input 14000>5000" && echo "PASS  per-agent overrun named" || { echo "FAIL  agent overrun"; fail=1; }
echo "$out" | grep -q "run: total" && echo "PASS  run total overrun named" || { echo "FAIL  run overrun"; fail=1; }

# coverage: drop reviewer from budgets -> unmetered agent flagged
python3 - <<'PY'
import json
b = json.load(open("budgets.json"))
del b["agents"]["reviewer"]
json.dump(b, open("budgets.nocover.json", "w"))
PY
out=$(python3 "$C" --traces-dir traces demo-run-001 --budgets budgets.nocover.json 2>&1); code=$?
rm -f budgets.nocover.json
[ $code -eq 1 ] && echo "$out" | grep -q "no budget" && echo "PASS  unbudgeted agent flagged" || { echo "FAIL  coverage"; fail=1; }

python3 "$C" --traces-dir traces no-such-run --budgets budgets.json >/dev/null 2>&1
[ $? -eq 2 ] && echo "PASS  missing trace fails loudly -> exit 2" || { echo "FAIL  input error"; fail=1; }

[ $fail -eq 0 ] && echo "SELFTEST OK" || echo "SELFTEST FAILED"
exit $fail
