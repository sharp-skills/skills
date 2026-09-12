#!/bin/sh
# Self-test for status-gates: every gate rule on the shipped registry.
cd "$(dirname "$0")" || exit 2
G=../scripts/status_gate.py
fail=0
expect() { want=$1; label=$2; shift 2
  python3 "$G" --registry registry.json --config gate-config.json "$@" >/dev/null 2>&1; got=$?
  [ "$got" -eq "$want" ] && echo "PASS  $label -> exit $want" || { echo "FAIL  $label (want $want, got $got)"; fail=1; }
}

expect 0 "registry publish-event routes"        --agent business_analyst --status BA_COMPLETE
expect 2 "invented status rejected"             --agent business_analyst --status SUCCESS
expect 0 "skip form allowed"                    --agent cto --status CTO_SKIPPED
expect 0 "shared failure terminal allowed"      --agent cto --status PIPELINE_FAILED
expect 0 "named observer exempt"                --agent event_bus --status DELIVERED
expect 0 "unknown agent fails open"             --agent stranger --status WHATEVER
expect 0 "no status emitted -> not applicable"  --agent business_analyst

# teaching rejection: the message must contain the allowed vocabulary
msg=$(python3 "$G" --registry registry.json --config gate-config.json --agent business_analyst --status SUCCESS 2>&1)
echo "$msg" | grep -q "BA_COMPLETE" && echo "PASS  rejection teaches the allowed vocabulary" || { echo "FAIL  rejection message"; fail=1; }

# reads the registry-ssot canonical shape (agents as a list of {id, publishes}) — one SSOT for both skills
python3 "$G" --registry registry.ssot-shape.json --agent cto --status TECHNICALLY_READY >/dev/null 2>&1
[ $? -eq 0 ] && echo "PASS  list-shaped (registry-ssot) registry routes" || { echo "FAIL  ssot-shape route"; fail=1; }
python3 "$G" --registry registry.ssot-shape.json --agent cto --status SUCCESS >/dev/null 2>&1
[ $? -eq 2 ] && echo "PASS  list-shaped registry rejects invented status" || { echo "FAIL  ssot-shape reject"; fail=1; }

[ $fail -eq 0 ] && echo "SELFTEST OK" || echo "SELFTEST FAILED"
exit $fail
