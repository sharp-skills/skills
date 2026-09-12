#!/bin/sh
# Self-test for observability-tracing: the shipped demo trace renders as a
# timeline and is discoverable via --list.
cd "$(dirname "$0")" || exit 2
V=../scripts/trace_view.py
fail=0

python3 "$V" --traces-dir traces demo-run-001 >/dev/null 2>&1
[ $? -eq 0 ] && echo "PASS  demo trace renders -> exit 0" || { echo "FAIL  demo trace"; fail=1; }

python3 "$V" --traces-dir traces --list 2>/dev/null | grep -q demo-run-001
[ $? -eq 0 ] && echo "PASS  --list finds the demo trace" || { echo "FAIL  --list"; fail=1; }

# red fixture: traces/corrupt-run.jsonl — a run killed mid-append leaves a
# truncated last line and no trace_end.
# fails because: interrupted append-only write (crashed run) — the viewer's
# contract is fail-open: it must neither crash on the bad line nor silently
# swallow it. Distinguishing signal = the [warn] naming the line, not exit 1.
out=$(python3 "$V" --traces-dir traces corrupt-run 2>&1); code=$?
[ $code -eq 0 ] && echo "PASS  corrupt trace renders fail-open -> exit 0" \
  || { echo "FAIL  corrupt trace (got $code)"; fail=1; }
echo "$out" | grep -q "\[warn\] line 3 malformed JSON" \
  && echo "PASS  malformed line reported, not swallowed" || { echo "FAIL  warn missing"; fail=1; }
echo "$out" | grep -q "analyst" \
  && echo "PASS  surviving events still rendered" || { echo "FAIL  surviving events"; fail=1; }

# a trace that does not exist is an error, not an empty render
python3 "$V" --traces-dir traces no-such-run >/dev/null 2>&1
[ $? -eq 1 ] && echo "PASS  missing trace -> exit 1" || { echo "FAIL  missing trace"; fail=1; }

[ $fail -eq 0 ] && echo "SELFTEST OK" || echo "SELFTEST FAILED"
exit $fail
