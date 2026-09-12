#!/usr/bin/env python3
"""
replay_check — lint an agent session's action log for replay safety.

A long-running session WILL be interrupted. Recovery must replay the log rather
than re-run it: anything non-deterministic has to come back from the record, and
anything with a real-world effect must not fire twice. This checker proves the
log can support that before you need it.

Usage:
  replay_check.py --actions actions.jsonl [--strict] [--quiet]

Exit codes:
  0  every action is replay-safe
  1  at least one violation
  2  usage / unreadable input (fail loud, never silently pass)

stdlib only, offline. It inspects the record, not the runtime, so it works for
any orchestrator that can emit one JSON object per action.
"""

import argparse
import json
import sys

# Kinds whose result cannot be reproduced by running them again. On recovery the
# recorded result must be replayed instead — re-running diverges the session.
NONDETERMINISTIC = {"user_prompt", "llm_call", "external_read", "random", "clock"}

# Kinds that touch the world. Replaying these repeats the effect, so each needs
# an idempotency key or an explicit "skip on replay" marker.
SIDE_EFFECTING = {"write", "payment", "email", "notify", "deploy"}

# Never safe to share across sessions: another user's answer is not yours.
NEVER_CACHEABLE = {"user_prompt"}

REQUIRED = ("session_id", "action_id", "kind", "status")


def is_side_effecting(rec):
    return rec.get("kind") in SIDE_EFFECTING or rec.get("side_effects") is True


def has_result(rec):
    """A recorded outcome, by value or by reference. `null` counts — an action
    can legitimately return nothing; what matters is that the key is present."""
    return "result" in rec or "result_ref" in rec


def check(rec, line_no, strict):
    """Return a list of violation strings for one action record."""
    out = []
    where = f"line {line_no}"

    for field in REQUIRED:
        if field not in rec:
            out.append(f"{where}: required field '{field}' missing")
    if out:
        return out  # shape is broken; further checks would be noise

    aid = rec["action_id"]
    kind = rec["kind"]
    status = rec["status"]
    where = f"{where} [{aid}]"

    # 1. Non-deterministic + succeeded -> the result must be in the log.
    if kind in NONDETERMINISTIC and status == "ok" and not has_result(rec):
        if kind == "user_prompt":
            out.append(
                f"{where}: user_prompt has no recorded result — recovery would "
                f"ask the human a question they already answered"
            )
        else:
            out.append(
                f"{where}: non-deterministic kind '{kind}' has no recorded "
                f"result — recovery would re-run it and diverge"
            )

    # 2. Side-effecting -> idempotency key, or explicitly skipped on replay.
    if is_side_effecting(rec) and status == "ok":
        if not rec.get("idempotency_key") and rec.get("replay") != "skip":
            out.append(
                f"{where}: side-effecting action has neither idempotency_key nor "
                f"replay=skip — recovery would repeat a real-world effect"
            )

    # 3. Retries must be bounded, and must not already have overrun.
    if rec.get("retryable") is True:
        cap = rec.get("max_attempts")
        if not isinstance(cap, int) or cap < 1:
            out.append(
                f"{where}: retryable action without a finite max_attempts — "
                f"an unbounded retry loop burns budget and never asks the human"
            )
        else:
            attempts = rec.get("attempts")
            if isinstance(attempts, int) and attempts > cap:
                out.append(
                    f"{where}: attempts {attempts} exceeds max_attempts {cap}"
                )

    # 4. Cache entries need a key and a lifetime; some kinds must never cache.
    if rec.get("cacheable") is True:
        if kind in NEVER_CACHEABLE:
            out.append(
                f"{where}: kind '{kind}' marked cacheable — a human's answer is "
                f"not shareable across sessions"
            )
        if not rec.get("cache_key"):
            out.append(f"{where}: cacheable action without a cache_key")
        ttl = rec.get("ttl_s")
        if not isinstance(ttl, int) or ttl <= 0:
            out.append(
                f"{where}: cacheable action without a positive ttl_s — a cache "
                f"entry that never expires is a stale answer waiting to happen"
            )

    # 5. Strict: an action that failed and is not retryable should say what
    #    happens next, so recovery is a decision and not a guess.
    if strict and status == "error" and not rec.get("retryable"):
        if not rec.get("on_failure"):
            out.append(
                f"{where}: failed non-retryable action without on_failure — "
                f"recovery has no instruction (ask_user / abort / compensate)"
            )

    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--actions", required=True, metavar="FILE",
                    help="JSONL action log, one action per line")
    ap.add_argument("--strict", action="store_true",
                    help="also require on_failure on failed non-retryable actions")
    ap.add_argument("--quiet", action="store_true",
                    help="print only the summary line")
    args = ap.parse_args()

    try:
        with open(args.actions, encoding="utf-8") as fh:
            lines = fh.readlines()
    except OSError as exc:
        print(f"cannot read {args.actions}: {exc}", file=sys.stderr)
        return 2

    violations = []
    seen_ids = set()
    checked = 0

    for i, raw in enumerate(lines, 1):
        raw = raw.strip()
        if not raw or raw.startswith("#"):
            continue
        try:
            rec = json.loads(raw)
        except json.JSONDecodeError as exc:
            violations.append(f"line {i}: not valid JSON ({exc.msg})")
            continue
        if not isinstance(rec, dict):
            violations.append(f"line {i}: expected an object")
            continue

        checked += 1
        aid = rec.get("action_id")
        if aid is not None:
            if aid in seen_ids:
                violations.append(
                    f"line {i} [{aid}]: duplicate action_id — replay cannot tell "
                    f"the two apart and would apply the wrong result"
                )
            seen_ids.add(aid)

        violations.extend(check(rec, i, args.strict))

    if violations and not args.quiet:
        for v in violations:
            print(v)
        print()

    if violations:
        print(f"replay-check FAIL: {len(violations)} violation(s) in "
              f"{checked} action(s)")
        return 1

    print(f"replay-check OK: {checked} action(s) replay-safe")
    return 0


if __name__ == "__main__":
    sys.exit(main())
