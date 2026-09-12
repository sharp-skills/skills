#!/bin/sh
# Self-test for eval-harness: exit codes, one golden per rubric dimension,
# and baseline regression detection. Stdlib only, no network.
cd "$(dirname "$0")" || exit 2
E=../scripts/eval_run.py
fail=0
expect() { # expect <exit_code> <label> <args...>
  want=$1; label=$2; shift 2
  python3 "$E" "$@" >/dev/null 2>&1
  got=$?
  [ "$got" -eq "$want" ] && echo "PASS  $label -> exit $want" || { echo "FAIL  $label (want $want, got $got)"; fail=1; }
}

# exit-code paths
expect 0 "healthy trace"                  --traces-dir traces demo-run-001
expect 1 "error status + missing fields"  --traces-dir traces weak-run
expect 2 "malformed JSONL"                --traces-dir traces broken-run

# goldens: one per rubric dimension
expect 1 "confidence below threshold"     --traces-dir traces golden-low-confidence
expect 1 "blocking alert label"           --traces-dir traces golden-alert-label
expect 1 "no scorable events"             --traces-dir traces golden-no-scorable
expect 0 "contract trace, default rubric" --traces-dir traces golden-contract
expect 1 "contract trace, strict rubric"  --traces-dir traces golden-contract --rubric rubric-contract.json

# baseline regression gate
expect 0 "healthy vs own baseline"        --traces-dir traces demo-run-001 --baseline baseline-demo.json
expect 1 "weak vs healthy baseline"       --traces-dir traces weak-run --baseline baseline-demo.json
expect 2 "missing baseline fails loudly"  --traces-dir traces demo-run-001 --baseline no-such-baseline.json

# --- grounding audit (fixtures under grounding/) ---
G=../scripts/grounding_check.py
python3 "$G" --output grounding/output.good.json --context grounding/context.json >/dev/null 2>&1
[ $? -eq 0 ] && echo "PASS  grounded output -> exit 0" || { echo "FAIL  grounding good"; fail=1; }

out=$(python3 "$G" --output grounding/output.bad.json --context grounding/context.json 2>&1); code=$?
[ $code -eq 1 ] && echo "PASS  hallucinated output -> exit 1" || { echo "FAIL  grounding bad (got $code)"; fail=1; }
echo "$out" | grep -q "b1: no citation" && echo "PASS  uncited claim caught" || { echo "FAIL  grounding uncited"; fail=1; }
echo "$out" | grep -q "b2:.*doesn't substantiate" && echo "PASS  mis-citation caught" || { echo "FAIL  grounding mis-cite"; fail=1; }
echo "$out" | grep -q "b3: cites source(s) \['s9'\].*fabricated" && echo "PASS  fabricated reference caught" || { echo "FAIL  grounding fabricated"; fail=1; }

python3 "$G" --output grounding/output.good.json --context no-such.json >/dev/null 2>&1
[ $? -eq 2 ] && echo "PASS  grounding missing context -> exit 2" || { echo "FAIL  grounding input error"; fail=1; }

# --- judge seam (--judge-cmd): a real verifier CLI, advisory, fails soft ---
# stub path unchanged: --judge with no cmd stays None
out=$(python3 "$E" --traces-dir traces demo-run-001 --judge 2>&1)
echo "$out" | grep -q "JUDGE_UNAVAILABLE" && echo "PASS  --judge stub still reports unavailable" || { echo "FAIL  judge stub"; fail=1; }

# real cmd: verdict is printed AND the structural exit code is unchanged
out=$(python3 "$E" --traces-dir traces demo-run-001 --judge-cmd "python3 fake_judge.py" 2>&1); code=$?
echo "$out" | grep -q '"label": "warn"' && echo "PASS  --judge-cmd verdict surfaced" || { echo "FAIL  judge verdict"; fail=1; }
[ "$code" -eq 0 ] && echo "PASS  judge is advisory: structural exit unchanged (0)" || { echo "FAIL  judge changed exit ($code)"; fail=1; }

# dead judge cmd fails soft — structural result still stands
python3 "$E" --traces-dir traces demo-run-001 --judge-cmd "/nonexistent-judge-bin" >/dev/null 2>&1
[ $? -eq 0 ] && echo "PASS  dead --judge-cmd fails soft -> exit 0" || { echo "FAIL  judge fail-soft"; fail=1; }

# --- entailment seam (--entailment-cmd): last-mile check on survivors, advisory ---
out=$(python3 "$G" --output grounding/output.good.json --context grounding/context.json --entailment-cmd "python3 fake_entailer.py" 2>&1); code=$?
echo "$out" | grep -q "does NOT fully entail.*ADVISORY" && echo "PASS  entailment surfaces the mis-entailment overlap can't catch" || { echo "FAIL  entailment advisory"; fail=1; }
[ "$code" -eq 0 ] && echo "PASS  entailment is advisory: grounded exit unchanged (0)" || { echo "FAIL  entailment changed exit ($code)"; fail=1; }

# dead entailer fails soft; a structural violation still gates regardless
python3 "$G" --output grounding/output.good.json --context grounding/context.json --entailment-cmd "/nonexistent" >/dev/null 2>&1
[ $? -eq 0 ] && echo "PASS  dead --entailment-cmd fails soft -> exit 0" || { echo "FAIL  entailment fail-soft"; fail=1; }
python3 "$G" --output grounding/output.bad.json --context grounding/context.json --entailment-cmd "python3 fake_entailer.py" >/dev/null 2>&1
[ $? -eq 1 ] && echo "PASS  structural gate still fires under entailment layer -> exit 1" || { echo "FAIL  structural gate under entailment"; fail=1; }

[ $fail -eq 0 ] && echo "SELFTEST OK" || echo "SELFTEST FAILED"
exit $fail
