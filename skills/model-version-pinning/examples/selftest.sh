#!/bin/sh
# Self-test for model-version-pinning: the checker passes a manifest that can
# survive a model release, and catches each way a plausible-looking manifest
# leaves a version change undetectable.
cd "$(dirname "$0")" || exit 2
C=../scripts/pin_check.py
fail=0

# a manifest that is pinned, probed and comparable -> 0
python3 "$C" --manifest models.good.json >/dev/null 2>&1
[ $? -eq 0 ] && echo "PASS  pinned manifest -> exit 0" || { echo "FAIL  clean case"; fail=1; }

# ...and it must also survive the stricter comparison check
python3 "$C" --manifest models.good.json --strict >/dev/null 2>&1
[ $? -eq 0 ] && echo "PASS  pinned manifest --strict -> exit 0" || { echo "FAIL  clean strict case"; fail=1; }

# the sick manifest -> 1, with every failure mode named
out=$(python3 "$C" --manifest models.bad.json 2>&1); code=$?
[ $code -eq 1 ] && echo "PASS  unpinned manifest -> exit 1" || { echo "FAIL  unpinned manifest (got $code)"; fail=1; }

echo "$out" | grep -q "floating marker 'latest'" \
  && echo "PASS  floating alias caught" || { echo "FAIL  floating-marker check"; fail=1; }
echo "$out" | grep -q "you named an alias" \
  && echo "PASS  silent alias drift caught (request != artifact)" || { echo "FAIL  resolved-mismatch check"; fail=1; }
echo "$out" | grep -q "no probe_set" \
  && echo "PASS  missing probe set caught" || { echo "FAIL  probe-set check"; fail=1; }
echo "$out" | grep -q "upgrade policy is auto" \
  && echo "PASS  auto-upgrade caught" || { echo "FAIL  upgrade-policy check"; fail=1; }
echo "$out" | grep -q "runtime not declared" \
  && echo "PASS  unpinned toolchain caught" || { echo "FAIL  runtime check"; fail=1; }

# a clean component must not be blamed for its neighbours
echo "$out" | grep -q "score-only:" && { echo "FAIL  score-only flagged without --strict"; fail=1; } \
  || echo "PASS  score-only clean by default"

# --strict adds the comparison-method check and nothing else
n=$(python3 "$C" --manifest models.bad.json --quiet 2>&1 | grep -o '[0-9]* violation' | cut -d' ' -f1)
s=$(python3 "$C" --manifest models.bad.json --strict --quiet 2>&1 | grep -o '[0-9]* violation' | cut -d' ' -f1)
[ "$s" -eq $((n + 1)) ] && echo "PASS  --strict adds exactly the compare check ($n -> $s)" \
  || { echo "FAIL  strict delta ($n -> $s)"; fail=1; }

python3 "$C" --manifest models.bad.json --strict 2>&1 | grep -q "declare 'trajectory'" \
  && echo "PASS  score-only comparison caught under --strict" || { echo "FAIL  compare check"; fail=1; }

# bad input must fail loud, not pass quietly
python3 "$C" --manifest no-such-file.json >/dev/null 2>&1
[ $? -eq 2 ] && echo "PASS  missing manifest -> exit 2 (fail loud)" || { echo "FAIL  missing-file handling"; fail=1; }

printf '{"components": []}' > .empty.json
python3 "$C" --manifest .empty.json >/dev/null 2>&1
[ $? -eq 2 ] && echo "PASS  empty manifest -> exit 2 (cannot pass by pinning nothing)" \
  || { echo "FAIL  empty-manifest handling"; fail=1; }
rm -f .empty.json

printf 'not json at all' > .broken.json
python3 "$C" --manifest .broken.json >/dev/null 2>&1
[ $? -eq 2 ] && echo "PASS  malformed manifest -> exit 2" || { echo "FAIL  malformed handling"; fail=1; }
rm -f .broken.json

[ $fail -eq 0 ] && echo "ALL PASS" || echo "FAILURES"
exit $fail
