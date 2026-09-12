#!/bin/sh
# Self-test for prompt-injection-guard: clean content passes; undelimited untrusted
# content and injection signatures are flagged.
cd "$(dirname "$0")" || exit 2
S=../scripts/injection_scan.py
fail=0

python3 "$S" --content content.good.jsonl >/dev/null 2>&1
[ $? -eq 0 ] && echo "PASS  clean content -> exit 0" || { echo "FAIL  good content"; fail=1; }

out=$(python3 "$S" --content content.bad.jsonl 2>&1); code=$?
[ $code -eq 1 ] && echo "PASS  hostile content -> exit 1" || { echo "FAIL  bad content (got $code)"; fail=1; }
echo "$out" | grep -q "b1: injection signature \[instruction override\]" && echo "PASS  override caught" || { echo "FAIL  override"; fail=1; }
echo "$out" | grep -q "b2: untrusted (web) content is not delimited" && echo "PASS  undelimited untrusted caught" || { echo "FAIL  delimit"; fail=1; }
echo "$out" | grep -q "b3: injection signature \[role/channel spoof\]" && echo "PASS  role spoof caught" || { echo "FAIL  role spoof"; fail=1; }
echo "$out" | grep -q "b4: injection signature \[embedded tool/role markup\]" && echo "PASS  tool markup caught" || { echo "FAIL  markup"; fail=1; }
echo "$out" | grep -q "b5: boundary escape" && echo "PASS  boundary escape caught (content contains its own marker)" || { echo "FAIL  boundary escape"; fail=1; }

# guessable marker: a warning by default (still exit 0), a hard finding under --strict
out=$(python3 "$S" --content content.weakmarker.jsonl 2>&1); code=$?
[ $code -eq 0 ] && echo "PASS  guessable marker is a warning, not a hard fail (exit 0)" || { echo "FAIL  weakmarker default (got $code)"; fail=1; }
echo "$out" | grep -q "w1: guessable delimiter" && echo "PASS  guessable marker warned" || { echo "FAIL  weakmarker warn"; fail=1; }
python3 "$S" --strict --content content.weakmarker.jsonl >/dev/null 2>&1
[ $? -eq 1 ] && echo "PASS  --strict promotes guessable marker to a finding (exit 1)" || { echo "FAIL  weakmarker strict"; fail=1; }

python3 "$S" --content no-such.jsonl >/dev/null 2>&1
[ $? -eq 2 ] && echo "PASS  missing file -> exit 2" || { echo "FAIL  input error"; fail=1; }

[ $fail -eq 0 ] && echo "SELFTEST OK" || echo "SELFTEST FAILED"
exit $fail
