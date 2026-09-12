#!/bin/sh
# Self-test for governance-hooks: blocks, allows, override, hook adapter, drift.
cd "$(dirname "$0")" || exit 2
G=../scripts/governance_check.py
fail=0
expect() { want=$1; label=$2; shift 2
  "$@" >/dev/null 2>&1; got=$?
  [ "$got" -eq "$want" ] && echo "PASS  $label -> exit $want" || { echo "FAIL  $label (want $want, got $got)"; fail=1; }
}

expect 0 "normal file edit allowed"      python3 "$G" no-touch src/main.py --config zones.json
expect 2 "no-touch zone blocked"         python3 "$G" no-touch config/registry.json --config zones.json
expect 2 "migrations glob blocked"       python3 "$G" no-touch migrations/001_init.sql --config zones.json
expect 2 "secret path read blocked"      python3 "$G" secret-read .env --config zones.json
expect 2 "secret-dumping command"        python3 "$G" secret-cmd "cat .env" --config zones.json
expect 0 "harmless command allowed"      python3 "$G" secret-cmd "ls -la" --config zones.json

GOVERNANCE_OVERRIDE=1 python3 "$G" no-touch config/registry.json --config zones.json >/dev/null 2>&1
[ $? -eq 0 ] && echo "PASS  named override honored -> exit 0" || { echo "FAIL  override"; fail=1; }

# hook adapter: JSON on stdin
printf '{"tool_name":"Edit","tool_input":{"file_path":"config/registry.json"}}' | python3 "$G" hook --config zones.json 2>/dev/null
[ $? -eq 2 ] && echo "PASS  hook blocks protected edit -> exit 2" || { echo "FAIL  hook block"; fail=1; }
printf '{"tool_name":"Edit","tool_input":{"file_path":"src/ok.py"}}' | python3 "$G" hook --config zones.json 2>/dev/null
[ $? -eq 0 ] && echo "PASS  hook allows normal edit -> exit 0" || { echo "FAIL  hook allow"; fail=1; }
printf 'not json' | python3 "$G" hook --config zones.json 2>/dev/null
[ $? -eq 0 ] && echo "PASS  unparseable hook input fails open -> exit 0" || { echo "FAIL  fail-open"; fail=1; }

# drift: snapshot, clean check, mutate, dirty check, restore
python3 "$G" drift-snapshot --config zones.json --lock /tmp/gov-demo.lock.json >/dev/null 2>&1 || { echo "FAIL  snapshot"; fail=1; }
expect 0 "drift clean after snapshot"    python3 "$G" drift-check --config zones.json --lock /tmp/gov-demo.lock.json
echo '{"setting": 2}' > demo/config/app.json
expect 2 "drift detected after edit"     python3 "$G" drift-check --config zones.json --lock /tmp/gov-demo.lock.json
echo '{"setting": 1}' > demo/config/app.json
rm -f /tmp/gov-demo.lock.json

[ $fail -eq 0 ] && echo "SELFTEST OK" || echo "SELFTEST FAILED"
exit $fail
