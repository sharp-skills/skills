#!/bin/sh
# Self-test for multi-agent-trust: legitimate messages pass; spoofing, privileged
# asks from untrusted tiers, and data-posing-as-orders are caught.
cd "$(dirname "$0")" || exit 2
C=../scripts/trust_check.py
fail=0

python3 "$C" --messages messages.good.jsonl >/dev/null 2>&1
[ $? -eq 0 ] && echo "PASS  legitimate messages -> exit 0" || { echo "FAIL  good messages"; fail=1; }

out=$(python3 "$C" --messages messages.bad.jsonl 2>&1); code=$?
[ $code -eq 1 ] && echo "PASS  hostile messages -> exit 1" || { echo "FAIL  bad messages (got $code)"; fail=1; }
echo "$out" | grep -q "b1: claims 'orchestrator'" && echo "PASS  spoofed source caught" || { echo "FAIL  spoof"; fail=1; }
echo "$out" | grep -q "b2: asks 'disable_safety' from tier 3" && echo "PASS  privileged ask from peer caught" || { echo "FAIL  privilege"; fail=1; }
echo "$out" | grep -q "b3: tier-4 'env' content carries instructions" && echo "PASS  data-as-orders caught" || { echo "FAIL  data-as-orders"; fail=1; }
echo "$out" | grep -q "b4: claims 'human'" && echo "PASS  forwarded-claims-human caught" || { echo "FAIL  b4 spoof"; fail=1; }

# unknown channel cannot be trusted
printf '%s\n' '{"id":"u","claimed_source":"human","channel":"telepathy","asks":["x"]}' > /tmp/mat_unknown.jsonl
out=$(python3 "$C" --messages /tmp/mat_unknown.jsonl 2>&1); code=$?
rm -f /tmp/mat_unknown.jsonl
[ $code -eq 1 ] && echo "PASS  unknown channel -> exit 1" || { echo "FAIL  unknown channel (got $code)"; fail=1; }
echo "$out" | grep -q "unknown channel" && echo "PASS  unknown channel named" || { echo "FAIL  unknown channel detail"; fail=1; }

python3 "$C" --messages no-such.jsonl >/dev/null 2>&1
[ $? -eq 2 ] && echo "PASS  missing file -> exit 2" || { echo "FAIL  input error"; fail=1; }

[ $fail -eq 0 ] && echo "SELFTEST OK" || echo "SELFTEST FAILED"
exit $fail
