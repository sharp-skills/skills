#!/bin/sh
# Self-test for durable-sessions: the checker passes a replay-safe log, and
# catches each way a plausible-looking log would break on recovery.
cd "$(dirname "$0")" || exit 2
C=../scripts/replay_check.py
fail=0

# a log that can be replayed -> 0
python3 "$C" --actions actions.good.jsonl >/dev/null 2>&1
[ $? -eq 0 ] && echo "PASS  replay-safe log -> exit 0" || { echo "FAIL  clean case"; fail=1; }

# the sick log -> 1, with every failure mode named
out=$(python3 "$C" --actions actions.bad.jsonl 2>&1); code=$?
[ $code -eq 1 ] && echo "PASS  unsafe log -> exit 1" || { echo "FAIL  unsafe log (got $code)"; fail=1; }

echo "$out" | grep -q "already answered" \
  && echo "PASS  unrecorded user_prompt caught" || { echo "FAIL  user_prompt check"; fail=1; }
echo "$out" | grep -q "'llm_call' has no recorded result" \
  && echo "PASS  unrecorded llm_call caught" || { echo "FAIL  nondeterminism check"; fail=1; }
echo "$out" | grep -q "repeat a real-world effect" \
  && echo "PASS  unkeyed payment caught" || { echo "FAIL  side-effect check"; fail=1; }
echo "$out" | grep -q "without a finite max_attempts" \
  && echo "PASS  unbounded retry caught" || { echo "FAIL  retry-cap check"; fail=1; }
echo "$out" | grep -q "attempts 7 exceeds max_attempts 3" \
  && echo "PASS  overrun retry caught" || { echo "FAIL  retry-overrun check"; fail=1; }
echo "$out" | grep -q "not shareable across sessions" \
  && echo "PASS  cached human answer caught" || { echo "FAIL  cache-scope check"; fail=1; }
echo "$out" | grep -q "without a positive ttl_s" \
  && echo "PASS  immortal cache entry caught" || { echo "FAIL  ttl check"; fail=1; }
echo "$out" | grep -q "duplicate action_id" \
  && echo "PASS  duplicate action_id caught" || { echo "FAIL  identity check"; fail=1; }
echo "$out" | grep -q "required field 'action_id' missing" \
  && echo "PASS  shapeless record caught" || { echo "FAIL  required-field check"; fail=1; }

# strict adds the dead-end check and nothing else
n=$(python3 "$C" --actions actions.bad.jsonl --quiet 2>&1 | grep -o '[0-9]* violation' | cut -d' ' -f1)
s=$(python3 "$C" --actions actions.bad.jsonl --strict --quiet 2>&1 | grep -o '[0-9]* violation' | cut -d' ' -f1)
[ "$s" -eq $((n + 1)) ] && echo "PASS  --strict adds exactly the on_failure check ($n -> $s)" \
  || { echo "FAIL  strict delta ($n -> $s)"; fail=1; }

# a missing file must fail loud, not pass quietly
python3 "$C" --actions no-such-file.jsonl >/dev/null 2>&1
[ $? -eq 2 ] && echo "PASS  unreadable input -> exit 2 (fail loud)" || { echo "FAIL  arg error"; fail=1; }

[ $fail -eq 0 ] && echo "ALL PASS" || echo "FAILURES"
exit $fail
