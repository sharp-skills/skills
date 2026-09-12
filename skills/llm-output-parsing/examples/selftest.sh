#!/bin/sh
# Self-test for llm-output-parsing: clean labeled prose extracts; conflicting
# values are flagged ambiguous (not guessed); missing/out-of-range are caught.
cd "$(dirname "$0")" || exit 2
P=../scripts/parse_output.py
fail=0

python3 "$P" --spec spec.json --output out.clean.txt >/dev/null 2>&1
[ $? -eq 0 ] && echo "PASS  clean labeled output -> exit 0" || { echo "FAIL  clean"; fail=1; }

out=$(python3 "$P" --spec spec.json --output out.ambiguous.txt 2>&1); code=$?
[ $code -eq 1 ] && echo "PASS  ambiguous output -> exit 1" || { echo "FAIL  ambiguous (got $code)"; fail=1; }
echo "$out" | grep -q "verdict: ambiguous (\['approve', 'reject'\])" && echo "PASS  conflicting verdict flagged, not guessed" || { echo "FAIL  ambiguity"; fail=1; }

out=$(python3 "$P" --spec spec.json --output out.problem.txt 2>&1); code=$?
[ $code -eq 1 ] && echo "PASS  problem output -> exit 1" || { echo "FAIL  problem (got $code)"; fail=1; }
echo "$out" | grep -q "verdict: not_found" && echo "PASS  missing verdict caught" || { echo "FAIL  not_found"; fail=1; }
echo "$out" | grep -q "score: invalid (150)" && echo "PASS  out-of-range number caught" || { echo "FAIL  invalid number"; fail=1; }
echo "$out" | grep -q "blocking = False" && echo "PASS  labeled boolean still extracted" || { echo "FAIL  boolean"; fail=1; }

python3 "$P" --spec no-such.json --output out.clean.txt >/dev/null 2>&1
[ $? -eq 2 ] && echo "PASS  missing spec -> exit 2" || { echo "FAIL  input error"; fail=1; }

# --- Half 2: mostly-JSON extract + validate (fixtures under json-validation/) ---
V=../scripts/output_validate.py
JV=json-validation
for f in out.clean.txt out.fenced.txt out.prose.txt out.trailingcomma.txt; do
  python3 "$V" --schema "$JV/out.schema.json" --output "$JV/$f" >/dev/null 2>&1
  [ $? -eq 0 ] && echo "PASS  json $f -> valid (0)" || { echo "FAIL  json $f should be valid"; fail=1; }
done

out=$(python3 "$V" --schema "$JV/out.schema.json" --output "$JV/out.badenum.txt" 2>&1); code=$?
[ $code -eq 1 ] && echo "PASS  json bad enum/bounds -> exit 1" || { echo "FAIL  json badenum (got $code)"; fail=1; }
echo "$out" | grep -q "not in enum" && echo "PASS  json enum violation reported" || { echo "FAIL  json enum detail"; fail=1; }
echo "$out" | grep -q "above maximum" && echo "PASS  json bound violation reported" || { echo "FAIL  json bound detail"; fail=1; }

out=$(python3 "$V" --schema "$JV/out.schema.json" --output "$JV/out.notjson.txt" 2>&1); code=$?
[ $code -eq 1 ] && echo "PASS  json prose (no JSON) -> exit 1" || { echo "FAIL  json notjson (got $code)"; fail=1; }
echo "$out" | grep -q "no JSON found" && echo "PASS  json re-ask cue given" || { echo "FAIL  json notjson detail"; fail=1; }

python3 "$V" --schema no-such.json --output "$JV/out.clean.txt" >/dev/null 2>&1
[ $? -eq 2 ] && echo "PASS  json missing schema -> exit 2" || { echo "FAIL  json input error"; fail=1; }

[ $fail -eq 0 ] && echo "SELFTEST OK" || echo "SELFTEST FAILED"
exit $fail
