#!/bin/sh
# Self-test for tool-call-validator: safe batch passes; each hazard is caught.
cd "$(dirname "$0")" || exit 2
C=../scripts/tool_call_check.py
fail=0

python3 "$C" --schema tools.json --calls calls.good.jsonl >/dev/null 2>&1
[ $? -eq 0 ] && echo "PASS  safe batch -> exit 0" || { echo "FAIL  good batch"; fail=1; }

out=$(python3 "$C" --schema tools.json --calls calls.bad.jsonl 2>&1); code=$?
[ $code -eq 1 ] && echo "PASS  unsafe batch -> exit 1" || { echo "FAIL  bad batch (got $code)"; fail=1; }
echo "$out" | grep -q "placeholder" && echo "PASS  placeholder arg caught" || { echo "FAIL  placeholder"; fail=1; }
echo "$out" | grep -q "destructive pattern 'rm -rf'" && echo "PASS  unapproved destructive caught" || { echo "FAIL  destructive"; fail=1; }
echo "$out" | grep -q "redundant" && echo "PASS  redundant repeat caught" || { echo "FAIL  redundant"; fail=1; }
echo "$out" | grep -q "missing required arg 'content'" && echo "PASS  missing arg caught" || { echo "FAIL  missing arg"; fail=1; }
echo "$out" | grep -q "delete_database' is not in the allowed schema" && echo "PASS  unknown tool caught" || { echo "FAIL  unknown tool"; fail=1; }

python3 "$C" --schema no-such.json --calls calls.good.jsonl >/dev/null 2>&1
[ $? -eq 2 ] && echo "PASS  missing schema -> exit 2" || { echo "FAIL  input error"; fail=1; }

# --- extractor: build the allowlist from a real MCP tool list, not by hand ---
X=../scripts/extract_tools.py
out=$(python3 "$X" mcp-tools.json 2>/dev/null)
echo "$out" | python3 -c "import json,sys;d=json.load(sys.stdin);assert set(d['tools'])=={'read_file','write_file','bash','http_get'};assert d['tools']['write_file']['required']==['path','content']" \
  && echo "PASS  extract_tools maps names + required args from MCP" || { echo "FAIL  extract map"; fail=1; }
# destructiveness is NOT guessed — flagged for review in two buckets:
#   general executors (bash) -> destructive_patterns; side-effecting names (write_file) -> destructive:true
echo "$out" | python3 -c "import json,sys;d=json.load(sys.stdin)['_needs_review'];assert d['general_executors']['tools']==['bash'];assert d['side_effecting']['tools']==['write_file']" \
  && echo "PASS  bash flagged as general-executor; write_file as side-effecting (neither auto-marked)" || { echo "FAIL  needs-review buckets"; fail=1; }
# the extracted schema feeds the REAL validator unchanged
python3 "$X" mcp-tools.json --out /tmp/tcv_tools.json 2>/dev/null
python3 "$C" --schema /tmp/tcv_tools.json --calls calls.good.jsonl >/dev/null 2>&1
[ $? -eq 0 ] && echo "PASS  extracted schema validates real calls -> exit 0" || { echo "FAIL  extracted validate"; fail=1; }
rm -f /tmp/tcv_tools.json

[ $fail -eq 0 ] && echo "SELFTEST OK" || echo "SELFTEST FAILED"
exit $fail
