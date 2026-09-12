#!/bin/sh
# Self-test for task-triage: routing, force rules, safe default, anti-stall.
cd "$(dirname "$0")" || exit 2
T=../scripts/triage.py
fail=0

out=$(python3 "$T" "write a blog post about our launch" --config triage-config.json --check-registry registry.json 2>/dev/null)
echo "$out" | grep -q '"template": "content"' && echo "$out" | grep -q '"n_agents": 3' \
  && echo "PASS  content goal -> short route, 3 agents, terminal reachable" \
  || { echo "FAIL  content route"; fail=1; }

out=$(python3 "$T" "add a billing endpoint with stripe" --config triage-config.json 2>/dev/null)
echo "$out" | grep -q '"legal"' && echo "PASS  billing goal -> legal group FORCED in" \
  || { echo "FAIL  force rule"; fail=1; }

out=$(python3 "$T" "сделай что-нибудь странное" --config triage-config.json 2>/dev/null)
echo "$out" | grep -q '"template": "full"' && echo "PASS  unknown goal -> full crew (safe default)" \
  || { echo "FAIL  safe default"; fail=1; }

out=$(python3 "$T" "оплата картой и персональные данные" --config triage-config.json 2>/dev/null)
echo "$out" | grep -q '"legal"' && echo "PASS  bilingual force rule (RU payments -> legal)" \
  || { echo "FAIL  bilingual rule"; fail=1; }

python3 "$T" "write a blog post" --config triage-config.stall.json --check-registry registry.json >/dev/null 2>&1
[ $? -eq 2 ] && echo "PASS  severed spine detected as stall -> exit 2" || { echo "FAIL  stall check"; fail=1; }

python3 "$T" "anything" --config triage-config.json --llm-cmd /nonexistent-classifier >/dev/null 2>&1
[ $? -eq 0 ] && echo "PASS  dead classifier fails soft to rules -> exit 0" || { echo "FAIL  fail-soft"; fail=1; }

[ $fail -eq 0 ] && echo "SELFTEST OK" || echo "SELFTEST FAILED"
exit $fail
