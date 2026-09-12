#!/bin/sh
# Self-test for adversarial-agent-review: a suite the agent withstands passes;
# succeeded attacks, a skipped probe, and a coverage gap are caught.
cd "$(dirname "$0")" || exit 2
C=../scripts/adversarial_check.py
fail=0

python3 "$C" --suite probes.json --responses responses.good.json >/dev/null 2>&1
[ $? -eq 0 ] && echo "PASS  agent withstood suite -> exit 0" || { echo "FAIL  good responses"; fail=1; }

out=$(python3 "$C" --suite probes.json --responses responses.bad.json 2>&1); code=$?
[ $code -eq 1 ] && echo "PASS  attacks succeeded -> exit 1" || { echo "FAIL  bad responses (got $code)"; fail=1; }
echo "$out" | grep -q "p1 (jailbreak): expected 'refuse', agent did 'comply'.*CRITICAL" && echo "PASS  critical jailbreak fail caught" || { echo "FAIL  critical fail"; fail=1; }
echo "$out" | grep -q "p4: no recorded response" && echo "PASS  skipped probe caught" || { echo "FAIL  skipped probe"; fail=1; }
echo "$out" | grep -q "CRITICAL failure present" && echo "PASS  critical gate reported" || { echo "FAIL  critical gate"; fail=1; }

# coverage gap: drop a required category's probe
python3 - <<'PY'
import json
s = json.load(open("probes.json"))
s["probes"] = [p for p in s["probes"] if p["category"] != "harmful_request"]
json.dump(s, open("/tmp/aar_gap.json","w"))
PY
out=$(python3 "$C" --suite /tmp/aar_gap.json --responses responses.good.json 2>&1); code=$?
rm -f /tmp/aar_gap.json
[ $code -eq 1 ] && echo "PASS  coverage gap -> exit 1" || { echo "FAIL  coverage gap (got $code)"; fail=1; }
echo "$out" | grep -q "coverage gap: required category 'harmful_request'" && echo "PASS  missing category caught" || { echo "FAIL  coverage detail"; fail=1; }

python3 "$C" --suite no-such.json --responses responses.good.json >/dev/null 2>&1
[ $? -eq 2 ] && echo "PASS  missing suite -> exit 2" || { echo "FAIL  input error"; fail=1; }

# ---- shipped STARTER SUITE (the asset): a real, provenance-bearing probe set ----
# An agent that withstands every probe passes; a single critical success fails;
# and every probe must carry provenance (a public attack class or a bundle demo),
# so the suite is a documented asset, not invented filler.
python3 "$C" --suite starter-suite.json --responses starter-responses.withstood.json >/dev/null 2>&1
[ $? -eq 0 ] && echo "PASS  starter suite withstood -> exit 0" || { echo "FAIL  starter withstood"; fail=1; }

python3 - <<'PY'
import json, sys
suite = json.load(open("starter-suite.json"))
resp  = json.load(open("starter-responses.withstood.json"))["responses"]
probes = suite["probes"]
# one critical attack succeeds -> the gate must fail
crit = next(p["id"] for p in probes if p["severity"] == "critical")
resp = dict(resp); resp[crit] = "comply"
json.dump({"responses": resp}, open("/tmp/aar_starter_breach.json", "w"))
# provenance present on every probe; required categories all covered
assert all(p.get("provenance") for p in probes), "a probe lacks provenance"
cats = {p["category"] for p in probes}
assert set(suite["required_categories"]) <= cats, "a required category is uncovered"
print(f"probes={len(probes)} categories={len(cats)}")
PY
[ $? -eq 0 ] && echo "PASS  every starter probe carries provenance; required categories covered" \
  || { echo "FAIL  provenance/coverage"; fail=1; }

python3 "$C" --suite starter-suite.json --responses /tmp/aar_starter_breach.json >/dev/null 2>&1
[ $? -eq 1 ] && echo "PASS  a critical success in the starter suite fails the gate -> exit 1" \
  || { echo "FAIL  starter breach"; fail=1; }
rm -f /tmp/aar_starter_breach.json

[ $fail -eq 0 ] && echo "SELFTEST OK" || echo "SELFTEST FAILED"
exit $fail
