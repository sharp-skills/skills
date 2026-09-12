#!/bin/sh
# Self-test for delegation-guards: a within-budget tree passes; depth, fan-out,
# cycle, and total-size breaches are caught.
cd "$(dirname "$0")" || exit 2
C=../scripts/delegation_check.py
fail=0

python3 "$C" --tree tree.good.json --policy policy.json >/dev/null 2>&1
[ $? -eq 0 ] && echo "PASS  within budget -> exit 0" || { echo "FAIL  good tree"; fail=1; }

out=$(python3 "$C" --tree tree.bad.json --policy policy.json 2>&1); code=$?
[ $code -eq 1 ] && echo "PASS  over budget -> exit 1" || { echo "FAIL  bad tree (got $code)"; fail=1; }
echo "$out" | grep -q "w: spawns 5 children" && echo "PASS  fan-out explosion caught" || { echo "FAIL  fanout"; fail=1; }
echo "$out" | grep -q "d4: delegation depth 4 exceeds" && echo "PASS  runaway depth caught" || { echo "FAIL  depth"; fail=1; }
echo "$out" | grep -q "delegation cycle detected" && echo "PASS  cycle caught" || { echo "FAIL  cycle"; fail=1; }
echo "$out" | grep -q "13 nodes (> max_total 12)" && echo "PASS  swarm-over-budget caught" || { echo "FAIL  total"; fail=1; }

# unresolved parent
printf '%s' '{"nodes":[{"id":"x","parent":"ghost"}]}' > /tmp/dg_ghost.json
out=$(python3 "$C" --tree /tmp/dg_ghost.json --policy policy.json 2>&1); code=$?
rm -f /tmp/dg_ghost.json
[ $code -eq 1 ] && echo "PASS  unresolved parent -> exit 1" || { echo "FAIL  ghost parent (got $code)"; fail=1; }
echo "$out" | grep -q "parent 'ghost' is not a known node" && echo "PASS  dangling parent named" || { echo "FAIL  ghost detail"; fail=1; }

# --- pre-spawn admission mode: gate one proposed spawn before it happens ---
python3 "$C" --tree tree.admit.json --policy policy.json --candidate parent=root >/dev/null 2>&1
[ $? -eq 0 ] && echo "PASS  admission ALLOW (root within budget) -> exit 0" || { echo "FAIL  admit allow"; fail=1; }

out=$(python3 "$C" --tree tree.admit.json --policy policy.json --candidate parent=p 2>&1); code=$?
[ $code -eq 1 ] && echo "PASS  admission DENY fan-out -> exit 1" || { echo "FAIL  admit fanout (got $code)"; fail=1; }
echo "$out" | grep -q "fan-out explosion" && echo "PASS  fan-out reason given" || { echo "FAIL  admit fanout reason"; fail=1; }

out=$(python3 "$C" --tree tree.admit.json --policy policy.json --candidate parent=deep3 2>&1); code=$?
[ $code -eq 1 ] && echo "PASS  admission DENY depth -> exit 1" || { echo "FAIL  admit depth (got $code)"; fail=1; }
echo "$out" | grep -q "depth 4 (> max_depth 3)" && echo "PASS  depth reason given" || { echo "FAIL  admit depth reason"; fail=1; }

out=$(python3 "$C" --tree tree.admit.json --policy policy.tighttotal.json --candidate parent=root 2>&1); code=$?
[ $code -eq 1 ] && echo "PASS  admission DENY total -> exit 1" || { echo "FAIL  admit total (got $code)"; fail=1; }
echo "$out" | grep -q "swarm over budget" && echo "PASS  total reason given" || { echo "FAIL  admit total reason"; fail=1; }

out=$(python3 "$C" --tree tree.admit.json --policy policy.json --candidate parent=ghost 2>&1); code=$?
[ $code -eq 1 ] && echo "PASS  admission DENY unknown parent -> exit 1" || { echo "FAIL  admit unknown (got $code)"; fail=1; }
echo "$out" | grep -q "not a known node" && echo "PASS  unknown-parent reason given" || { echo "FAIL  admit unknown reason"; fail=1; }

python3 "$C" --tree tree.admit.json --policy policy.json --candidate bogus >/dev/null 2>&1
[ $? -eq 2 ] && echo "PASS  malformed candidate spec -> exit 2" || { echo "FAIL  admit malformed"; fail=1; }

python3 "$C" --tree no-such.json --policy policy.json >/dev/null 2>&1
[ $? -eq 2 ] && echo "PASS  missing tree -> exit 2" || { echo "FAIL  input error"; fail=1; }

# --- extractor: reconstruct the tree from a real trace, then audit it ---
# You don't hand-write spawns.json; the trace already has the parent links.
X=../scripts/extract_spawns.py
python3 "$X" spawns-trace.jsonl --out /tmp/dg_spawns.json 2>/dev/null
[ $? -eq 0 ] && echo "PASS  extract_spawns builds a tree from a trace" || { echo "FAIL  extract"; fail=1; }
# 5 agent-turn spans; the tool_call span is NOT a spawn and is skipped
n=$(python3 -c "import json;print(len(json.load(open('/tmp/dg_spawns.json'))['nodes']))")
[ "$n" -eq 5 ] && echo "PASS  tool-call span excluded (5 nodes, not 6)" || { echo "FAIL  node count ($n)"; fail=1; }
# the extracted tree feeds the REAL checker unchanged
python3 "$C" --tree /tmp/dg_spawns.json --policy policy.json >/dev/null 2>&1
[ $? -eq 0 ] && echo "PASS  extracted tree audits within budget -> exit 0" || { echo "FAIL  extracted audit"; fail=1; }
rm -f /tmp/dg_spawns.json

[ $fail -eq 0 ] && echo "SELFTEST OK" || echo "SELFTEST FAILED"
exit $fail
