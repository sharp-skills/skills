#!/usr/bin/env python3
"""Two-layer critic policy: tier routing + review-output validation.

Policy (critic-policy.json):
  {"tiers": {"FAST": null, "STANDARD": "cheap", "DEEP": "premium"},
   "max_findings": 3,
   "required_finding_fields": ["severity", "location", "claim", "fix_direction"],
   "severities": ["HIGH", "MEDIUM", "LOW"],
   "verdicts": ["PASS", "FAIL"]}

Subcommands:
  route     --mode X       -> prints the reviewing tier, or "skip" (null tier)
  validate  review.json    -> checks cap, structure, verdict

Review output shape:
  {"verdict": "FAIL",
   "findings": [{"severity": "HIGH", "location": "blueprint §3",
                 "claim": "auth flow lacks a revocation path",
                 "fix_direction": "add revoke endpoint to the token design"}]}

Exit codes: 0 ok · 1 policy violation · 2 bad input. Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DEFAULT_POLICY = {
    "tiers": {"FAST": None, "STANDARD": "cheap", "DEEP": "premium"},
    "max_findings": 3,
    "required_finding_fields": ["severity", "location", "claim", "fix_direction"],
    "severities": ["HIGH", "MEDIUM", "LOW"],
    "verdicts": ["PASS", "FAIL"],
}


def die(msg: str) -> "NoReturn":
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(2)


def load_policy(path: str | None) -> dict:
    policy = dict(DEFAULT_POLICY)
    if path:
        try:
            policy.update(json.loads(Path(path).read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError) as exc:
            die(f"cannot read policy {path}: {exc}")
    return policy


def cmd_route(args) -> int:
    policy = load_policy(args.policy)
    tiers = policy.get("tiers") or {}
    if args.mode not in tiers:
        die(f"unknown mode {args.mode!r}; policy modes: {sorted(tiers)}")
    tier = tiers[args.mode]
    if tier is None:
        print("skip  (a fast track with mandatory review is not a fast track)")
    else:
        print(tier)
    return 0


def cmd_validate(args) -> int:
    policy = load_policy(args.policy)
    try:
        review = json.loads(Path(args.review).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        die(f"cannot read review {args.review}: {exc}")
    if not isinstance(review, dict):
        die("review output must be a JSON object")

    violations: list[str] = []

    verdict = review.get("verdict")
    if verdict not in set(policy.get("verdicts") or []):
        violations.append(
            f"verdict {verdict!r} — must be one of {policy['verdicts']}; "
            f"scores invite negotiation, pass/fail invites fixes")

    findings = review.get("findings")
    if not isinstance(findings, list):
        violations.append("findings must be a list (structured or it didn't happen)")
        findings = []
    cap = int(policy.get("max_findings", 3))
    if len(findings) > cap:
        violations.append(
            f"{len(findings)} findings > cap {cap} — an uncapped reviewer "
            f"pads with trivia; spend the cap on what matters")
    if verdict == "FAIL" and not findings:
        violations.append("FAIL with zero findings — a fail must name its reasons")

    required = policy.get("required_finding_fields") or []
    severities = set(policy.get("severities") or [])
    for i, f in enumerate(findings, 1):
        if not isinstance(f, dict):
            violations.append(f"finding {i}: not an object")
            continue
        for field in required:
            if not f.get(field):
                violations.append(f"finding {i}: missing/empty {field!r}")
        sev = f.get("severity")
        if severities and sev not in severities:
            violations.append(f"finding {i}: severity {sev!r} not in {sorted(severities)}")

    if violations:
        print(f"{len(violations)} policy violation(s):", file=sys.stderr)
        for v in violations:
            print(f"  ✗ {v}", file=sys.stderr)
        return 1
    print(f"✅ review output satisfies policy "
          f"({len(findings)} finding(s), verdict {verdict})")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("route", help="run mode -> reviewing tier (or skip)")
    r.add_argument("--mode", required=True)
    r.add_argument("--policy")
    r.set_defaults(fn=cmd_route)

    v = sub.add_parser("validate", help="check a review output against the policy")
    v.add_argument("review")
    v.add_argument("--policy")
    v.set_defaults(fn=cmd_validate)

    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
