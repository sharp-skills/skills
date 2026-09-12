#!/bin/sh
# Self-test for mechanize-agents: the runtime audit catches every flip hazard.
cd "$(dirname "$0")" || exit 2
A=../scripts/runtime_audit.py
fail=0

python3 "$A" --registry registry.json --manifest handlers.good.json >/dev/null 2>&1
[ $? -eq 0 ] && echo "PASS  complete manifest -> exit 0" || { echo "FAIL  good manifest"; fail=1; }

out=$(python3 "$A" --registry registry.json --manifest handlers.broken.json 2>&1); code=$?
[ $code -eq 1 ] && echo "PASS  broken manifest -> exit 1" || { echo "FAIL  broken manifest (got $code)"; fail=1; }
echo "$out" | grep -q "session_mgr" && echo "PASS  missing handler caught" || { echo "FAIL  missing handler"; fail=1; }
echo "$out" | grep -q "GITHUB_FORCE_PUSHED" && echo "PASS  unregistered event caught" || { echo "FAIL  event check"; fail=1; }
echo "$out" | grep -q "defer_status 'ANALYSIS_COMPLETE' is a registry event" && echo "PASS  defer-as-bus-event caught" || { echo "FAIL  defer check"; fail=1; }
echo "$out" | grep -q "ghost_agent" && echo "PASS  unknown-agent handler fails loudly" || { echo "FAIL  ghost handler"; fail=1; }

python3 "$A" --registry no-such.json --manifest handlers.good.json >/dev/null 2>&1
[ $? -eq 2 ] && echo "PASS  missing registry fails loudly -> exit 2" || { echo "FAIL  input error"; fail=1; }

[ $fail -eq 0 ] && echo "SELFTEST OK" || echo "SELFTEST FAILED"
exit $fail
