#!/bin/sh
# One command, whole-bundle audit: run every skill's self-test and both
# composition demos, aggregate the result, exit non-zero if anything fails.
# This is the loop you'd otherwise run by hand, once per skill. Skills are
# discovered from the tree (*/examples/selftest.sh), so the count is never
# hardcoded and the script does not go stale as the bundle grows.
# Stdlib/POSIX only, offline, deterministic.
#
#   sh bundle_check.sh            # selftests + demos
#   sh bundle_check.sh --scrub    # also run the pre-publish scrub gate, if available
#
# The scrub gate lives outside the shipped bundle (it needs a private name list),
# so --scrub is best-effort: it runs when SCRUB_GATE + SCRUB_PATTERNS resolve,
# and is reported as SKIPPED otherwise — never a silent pass.
cd "$(dirname "$0")" || exit 2

# Where the skills are: siblings of this script in the source repo, or
# ../../skills/ when shipped inside a library as bundles/<name>/.
if [ -d ../../skills ] && [ ! -d ./registry-ssot ]; then S=../../skills; else S=.; fi

want_scrub=0
[ "$1" = "--scrub" ] && want_scrub=1

pass=0; failn=0; failed=""
run() { # run <label> <cmd...>
  label=$1; shift
  if "$@" >/dev/null 2>&1; then
    pass=$((pass + 1))
  else
    failn=$((failn + 1)); failed="$failed $label"
    echo "  FAIL  $label"
  fi
}

echo "=================================================================="
echo " multi-agent-engineering — bundle audit"
echo "=================================================================="

echo
echo "self-tests:"
for st in "$S"/*/examples/selftest.sh; do
  skill=$(basename "$(dirname "$(dirname "$st")")")
  run "$skill" sh "$st"
done
selftests=$((pass + failn))
echo "  -> $pass/$selftests self-tests passed"

echo
echo "composition demos:"
demo_fail=0
for d in demo/demo.sh demo-security/demo-security.sh; do
  if [ -f "$d" ]; then
    if sh "$d" >/dev/null 2>&1; then
      echo "  PASS  $d"
    else
      echo "  FAIL  $d"; demo_fail=1
    fi
  fi
done

scrub_status="skipped"
if [ "$want_scrub" -eq 1 ]; then
  echo
  echo "scrub gate:"
  # resolve the gate + patterns from env or the conventional launch/ location
  GATE=${SCRUB_GATE:-../launch/scrub_gate.py}
  PATS=${SCRUB_PATTERNS:-../launch/scrub-patterns.txt}
  if [ -f "$GATE" ] && [ -f "$PATS" ]; then
    if python3 "$GATE" --target . --patterns "$PATS"; then
      echo "  PASS  no private names in the bundle"; scrub_status="pass"
    else
      echo "  FAIL  scrub gate found private names"; scrub_status="fail"
    fi
  else
    echo "  SKIPPED  gate or patterns not found (GATE=$GATE PATS=$PATS)"
    echo "           set SCRUB_GATE / SCRUB_PATTERNS to enable"
  fi
fi

echo
echo "------------------------------------------------------------------"
ok=1
[ "$failn" -eq 0 ] || { echo "FAILED self-tests:$failed"; ok=0; }
[ "$demo_fail" -eq 0 ] || { echo "FAILED demos"; ok=0; }
[ "$scrub_status" = "fail" ] && { echo "FAILED scrub"; ok=0; }
if [ "$ok" -eq 1 ]; then
  echo "BUNDLE OK — $selftests self-tests + 2 demos green (scrub: $scrub_status)"
  exit 0
fi
echo "BUNDLE FAILED"
exit 1
