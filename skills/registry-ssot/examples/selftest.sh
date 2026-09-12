#!/bin/sh
# Self-test for registry-ssot: proves the validator catches wiring drift.
# Expected: good registry exits 0; planted orphan subs / dead-ends / bus drift exit 1.
cd "$(dirname "$0")" || exit 2
V=../scripts/validate_registry.py
fail=0

python3 "$V" registry.good.json >/dev/null 2>&1
[ $? -eq 0 ] && echo "PASS  consistent registry -> exit 0" || { echo "FAIL  good registry rejected"; fail=1; }

python3 "$V" registry.bad.json >/dev/null 2>&1
[ $? -eq 1 ] && echo "PASS  orphan subs + dead-ends + bus drift -> exit 1" || { echo "FAIL  defects not caught"; fail=1; }

[ $fail -eq 0 ] && echo "SELFTEST OK" || echo "SELFTEST FAILED"
exit $fail
