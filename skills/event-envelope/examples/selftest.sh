#!/bin/sh
# Self-test for event-envelope: the checker proves the runtime enums are a pair
# and rejects malformed envelopes on the wire.
cd "$(dirname "$0")" || exit 2
C=../scripts/envelope_check.py
fail=0

# aligned enum + well-formed stream -> 0
python3 "$C" --schema envelope.schema.json --runtimes-source runtimes.source \
  --events envelopes.good.jsonl >/dev/null 2>&1
[ $? -eq 0 ] && echo "PASS  aligned enum + good stream -> exit 0" || { echo "FAIL  clean case"; fail=1; }

# drift: dispatcher gained a runtime the schema lacks -> 1
out=$(python3 "$C" --schema envelope.schema.json --runtimes-source runtimes.drifted.source 2>&1); code=$?
[ $code -eq 1 ] && echo "PASS  runtime drift -> exit 1" || { echo "FAIL  drift (got $code)"; fail=1; }
echo "$out" | grep -q "remote-gpu" && echo "PASS  missing runtime named" || { echo "FAIL  drift detail"; fail=1; }

# malformed envelopes -> 1, each flaw caught
out=$(python3 "$C" --schema envelope.schema.json --events envelopes.bad.jsonl 2>&1); code=$?
[ $code -eq 1 ] && echo "PASS  bad stream -> exit 1" || { echo "FAIL  bad stream (got $code)"; fail=1; }
echo "$out" | grep -q "required field 'trace_id'" && echo "PASS  missing trace_id caught" || { echo "FAIL  required check"; fail=1; }
echo "$out" | grep -q "gpu-farm" && echo "PASS  unknown runtime caught" || { echo "FAIL  runtime check"; fail=1; }
echo "$out" | grep -q "pipeline_mode 'TURBO'" && echo "PASS  unknown mode caught" || { echo "FAIL  mode check"; fail=1; }
echo "$out" | grep -q "confidence_score must be" && echo "PASS  out-of-range score caught" || { echo "FAIL  score check"; fail=1; }

# no work requested -> loud input error
python3 "$C" --schema envelope.schema.json >/dev/null 2>&1
[ $? -eq 2 ] && echo "PASS  nothing to check -> exit 2" || { echo "FAIL  input error"; fail=1; }

[ $fail -eq 0 ] && echo "SELFTEST OK" || echo "SELFTEST FAILED"
exit $fail
