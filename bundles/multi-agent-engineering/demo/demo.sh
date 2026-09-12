#!/bin/sh
# End-to-end demo: one small multi-agent run wired through five bundle skills over
# ONE shared registry and ONE trace. Stdlib Python only, offline, deterministic.
# `sh demo.sh` exits 0 iff the composition behaves as designed.
cd "$(dirname "$0")" || exit 2
# skills: siblings of this demo in the source repo, ../../../skills when shipped in a library
if [ -d ../../../skills ] && [ ! -d ../registry-ssot ]; then B=../../../skills; else B=..; fi
TRACES=.context/traces
REG=registry.json
fail=0
line() { echo "------------------------------------------------------------"; }

echo "############################################################"
echo "# multi-agent-engineering — end-to-end composition demo"
echo "############################################################"

line; echo "STEP 1  registry-ssot — validate the shared registry (the single source of truth)"
python3 "$B"/registry-ssot/scripts/validate_registry.py "$REG" || { echo "  registry invalid"; fail=1; }

line; echo "STEP 2  run the pipeline — routing DERIVED from the registry, each status gated by status-gates, each step traced"
python3 run_pipeline.py --registry "$REG" --out "$TRACES" --trace-id demo-e2e-001 || { echo "  happy-path pipeline failed"; fail=1; }

line; echo "STEP 3  observability-tracing — replay the recorded run"
python3 "$B"/observability-tracing/scripts/trace_view.py demo-e2e-001 --traces-dir "$TRACES" || fail=1

line; echo "STEP 4  eval-harness — score the recorded outputs (structural rubric)"
python3 "$B"/eval-harness/scripts/eval_run.py demo-e2e-001 --traces-dir "$TRACES" || { echo "  eval gate failed"; fail=1; }

line; echo "STEP 5  cost-budgeting — check the same trace against per-agent budgets"
python3 "$B"/cost-budgeting/scripts/budget_check.py demo-e2e-001 --traces-dir "$TRACES" --budgets budgets.json || { echo "  over budget"; fail=1; }

line; echo "STEP 6  status-gates (failure path) — engineer emits an unroutable status; the gate rejects it and the run fails LOUDLY instead of stalling silently"
python3 run_pipeline.py --registry "$REG" --out "$TRACES" --trace-id demo-e2e-bad --inject-bad-status
bad=$?
if [ "$bad" -eq 1 ]; then
  echo "  as designed: the unroutable status was rejected and the pipeline stopped with PIPELINE_FAILED (exit 1)"
else
  echo "  FAIL: the bad-status run should have been rejected (expected exit 1, got $bad)"
  fail=1
fi

line
if [ "$fail" -eq 0 ]; then
  echo "DEMO OK — five skills composed over one registry and one trace."
else
  echo "DEMO FAILED"
fi
exit $fail
