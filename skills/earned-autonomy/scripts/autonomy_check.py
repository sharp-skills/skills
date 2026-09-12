#!/usr/bin/env python3
"""
autonomy_check — audit the grants that decide what an agent may do without asking.

Autonomy is not a setting, it is a position on a ladder, and the only defensible
way up is a track record a human produced. This checker reads a grant ledger —
one record per (action, resource, principal) — and refuses the six shapes that
let an agent hold authority nobody deliberately gave it.

The invariant everything else rests on: **an agent cannot grant itself.** If the
ledger can be written by the thing it governs, every other check is decoration.

Usage:
  autonomy_check.py --grants grants.jsonl [--min-streak N] [--strict] [--quiet]

Exit codes:
  0  every grant is earned, scoped and reviewable
  1  at least one violation
  2  usage / unreadable / malformed input (fail loud, never silently pass)

stdlib only, offline. It inspects the ledger, not the runtime, so any system that
can emit one JSON object per grant is supported.
"""

import argparse
import json
import sys

# The ladder, lowest authority first. Each rung is a different answer to
# "what happens when the agent decides to act?"
RUNGS = ("observe", "propose", "ask", "act")

# Rungs at which the agent may cause an effect outside itself without a human
# looking at that specific instance first.
AUTONOMOUS = {"act"}

# Verdicts a human can return on a proposal. Only one of them is clean.
CLEAN_VERDICT = "accepted"
KNOWN_VERDICTS = {CLEAN_VERDICT, "edited", "rejected", "ignored"}

DEFAULT_MIN_STREAK = 10

REQUIRED = ("grant_id", "action", "resource", "principal", "rung", "granted_by")


def trailing_clean_streak(verdicts):
    """Consecutive clean verdicts counting back from the most recent.

    Trailing, never total: the streak is evidence that the agent is trustworthy
    *now*. One edit resets it, which is the whole point — a counter that only
    accumulates rewards an agent for being right a long time ago.
    """
    streak = 0
    for verdict in reversed(verdicts):
        if verdict == CLEAN_VERDICT:
            streak += 1
        else:
            break
    return streak


def check_grant(grant, min_streak, strict):
    """Yield human-readable violations for one grant record."""
    where = grant.get("grant_id")
    action = grant.get("action", "")
    resource = grant.get("resource", "")
    rung = grant.get("rung")

    # 0. The rung has to be on the ladder at all.
    if rung not in RUNGS:
        yield (
            f"{where}: rung '{rung}' is not on the ladder "
            f"({', '.join(RUNGS)}) — an unrecognised rung is enforced by nothing"
        )
        return

    # 1. THE invariant: a grant is something a human hands over.
    granted_by = grant.get("granted_by", "")
    if not granted_by.startswith("human:"):
        actor = granted_by or "nobody"
        yield (
            f"{where}: granted_by is '{actor}' — authority must be conferred by a human "
            f"principal. An agent that can write this ledger has unbounded authority "
            f"regardless of what the rung says"
        )

    # 2. Autonomy is earned from a trailing run of clean human verdicts.
    evidence = grant.get("evidence") or {}
    verdicts = evidence.get("verdicts") or []
    streak = trailing_clean_streak(verdicts)
    if rung in AUTONOMOUS and streak < min_streak:
        yield (
            f"{where}: rung '{rung}' with a trailing clean streak of {streak} "
            f"(needs {min_streak}) — promotion has to be paid for by a track record, "
            f"and one edited or rejected proposal resets the count"
        )

    # 3. The track record must belong to THIS grant.
    scope = evidence.get("scope")
    expected = f"{action}@{resource}"
    if rung in AUTONOMOUS and scope != expected:
        got = scope if scope else "not declared"
        yield (
            f"{where}: evidence scope is {got} but this grant covers {expected} — "
            f"a record earned somewhere else is not evidence for acting here"
        )

    # 4. Scope: the same verb on two resources is two different risks.
    if not resource or resource == "*":
        yield (
            f"{where}: resource is '{resource or 'missing'}' — grants key on "
            f"(action, resource, principal). '{action}' against a harmless target and "
            f"against a consequential one are not the same permission"
        )

    # 5. A proposal rung that can cause an effect is a contradiction.
    if rung in ("observe", "propose") and grant.get("side_effect") is True:
        yield (
            f"{where}: rung '{rung}' with side_effect true — at this rung the agent "
            f"produces a proposal (a draft, a pull request, a queued item), never the "
            f"effect itself. Otherwise the rung guarantees nothing"
        )

    # 6. Asking in a channel nobody reads is not a safeguard.
    channel = grant.get("review_channel") or {}
    if rung == "ask" and channel.get("watched") is not True:
        name = channel.get("name", "unnamed")
        yield (
            f"{where}: rung 'ask' routes to '{name}', which is not marked watched — "
            f"an approval request in an unwatched channel means the action never "
            f"happens. Either mark the channel watched, or move to a rung that "
            f"does not depend on someone looking"
        )

    # 7. (--strict) A grant with no review date drifts forever.
    if strict and not grant.get("expires"):
        yield (
            f"{where}: no expires — authority granted once and never revisited "
            f"outlives the conditions that justified it"
        )


def load(path):
    """Read the ledger, or exit 2. Malformed input must never pass quietly."""
    grants = []
    try:
        with open(path, encoding="utf-8") as handle:
            for number, line in enumerate(handle, start=1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    sys.stderr.write(f"autonomy_check: {path}:{number} is not valid JSON: {exc}\n")
                    raise SystemExit(2)
                if not isinstance(record, dict):
                    sys.stderr.write(f"autonomy_check: {path}:{number} is not an object\n")
                    raise SystemExit(2)
                grants.append((number, record))
    except FileNotFoundError:
        sys.stderr.write(f"autonomy_check: no such ledger: {path}\n")
        raise SystemExit(2)

    if not grants:
        sys.stderr.write(
            f"autonomy_check: {path} contains no grants — an empty ledger would pass "
            f"every check while governing nothing\n"
        )
        raise SystemExit(2)
    return grants


def main():
    parser = argparse.ArgumentParser(
        description="Audit an agent authority ledger: earned, scoped, human-granted, reviewable."
    )
    parser.add_argument("--grants", required=True, help="path to the grant ledger JSONL")
    parser.add_argument(
        "--min-streak",
        type=int,
        default=DEFAULT_MIN_STREAK,
        help=f"clean verdicts required to hold an autonomous rung (default {DEFAULT_MIN_STREAK})",
    )
    parser.add_argument(
        "--strict", action="store_true", help="also require an expiry/review date on every grant"
    )
    parser.add_argument("--quiet", action="store_true", help="print the summary line only")
    args = parser.parse_args()

    if args.min_streak < 1:
        sys.stderr.write("autonomy_check: --min-streak must be at least 1\n")
        raise SystemExit(2)

    grants = load(args.grants)

    violations = []
    seen = set()

    for number, grant in grants:
        missing = [field for field in REQUIRED if field not in grant]
        if missing:
            sys.stderr.write(
                f"autonomy_check: line {number} missing required field(s): {', '.join(missing)}\n"
            )
            raise SystemExit(2)

        ident = grant["grant_id"]
        if ident in seen:
            sys.stderr.write(f"autonomy_check: duplicate grant_id '{ident}' at line {number}\n")
            raise SystemExit(2)
        seen.add(ident)

        for verdict in (grant.get("evidence") or {}).get("verdicts") or []:
            if verdict not in KNOWN_VERDICTS:
                sys.stderr.write(
                    f"autonomy_check: line {number} has unknown verdict '{verdict}' "
                    f"(expected one of {', '.join(sorted(KNOWN_VERDICTS))})\n"
                )
                raise SystemExit(2)

        violations.extend(check_grant(grant, args.min_streak, args.strict))

    if violations and not args.quiet:
        for violation in violations:
            print(f"  ✗ {violation}")

    count = len(violations)
    if count:
        print(f"autonomy_check: {count} violation{'s' if count != 1 else ''} "
              f"across {len(grants)} grant(s)")
        return 1

    print(f"autonomy_check: {len(grants)} grant(s) earned, scoped and reviewable")
    return 0


if __name__ == "__main__":
    sys.exit(main())
