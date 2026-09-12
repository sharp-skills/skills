#!/usr/bin/env python3
"""Verify a hand-off artifact: deterministic floor + optional cross-model layer.

Layer 1 (always, $0, stdlib): against a spec —
  * required fields present and non-empty;
  * mechanical contradictions: an item appearing in two fields declared
    conflicting (e.g. no_touch_zones vs files_to_modify).

Layer 2 (optional, fails SOFT): --verifier-cmd runs an external model CLI
(prompt appended as the last argument) that returns a JSON verdict
  {"gaps": ["..."], "contradictions": ["..."]}
against the --upstream source. A dead/absent/malformed verifier NEVER fails
the check — it degrades to the deterministic floor with a note (control arm).

Spec (handoff-spec.json):
  {"required_fields": ["objective", "files_to_modify", "no_touch_zones",
                       "acceptance_criteria"],
   "conflict_pairs": [["no_touch_zones", "files_to_modify"]]}

Exit codes: 0 = complete & consistent, 1 = gaps/contradictions, 2 = bad input.
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path


def die(msg: str) -> "NoReturn":
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(2)


def load(path: str, what: str) -> dict:
    try:
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        die(f"cannot read {what} {path}: {exc}")
    if not isinstance(doc, dict):
        die(f"{what} must be a JSON object: {path}")
    return doc


def is_empty(v) -> bool:
    return v is None or v == "" or v == [] or v == {}


def as_items(v) -> set[str]:
    if isinstance(v, list):
        return {str(x) for x in v}
    if isinstance(v, str) and v:
        return {v}
    return set()


def deterministic_floor(handoff: dict, spec: dict) -> list[str]:
    findings: list[str] = []
    for f in spec.get("required_fields") or []:
        if f not in handoff:
            findings.append(f"GAP: required field {f!r} is missing")
        elif is_empty(handoff[f]):
            findings.append(f"GAP: required field {f!r} is empty — an empty "
                            f"no-touch/criteria list is a decision, state it upstream")
    for a, b in spec.get("conflict_pairs") or []:
        overlap = as_items(handoff.get(a)) & as_items(handoff.get(b))
        for item in sorted(overlap):
            findings.append(f"CONTRADICTION: {item!r} appears in both {a!r} "
                            f"and {b!r} — downstream cannot obey both")
    return findings


def cross_model_layer(handoff: dict, upstream: dict | None, cmd: str,
                      spec: dict) -> tuple[list[str], list[str]]:
    """Returns (findings, notes). Fails SOFT: any problem -> ([], [note])."""
    fields = ", ".join(spec.get("required_fields") or [])
    prompt = (
        "You are an independent auditor (NOT the author). Decide ONLY whether "
        "this hand-off is COMPLETE and INTERNALLY CONSISTENT against the "
        "upstream source. Do not rewrite it; do not judge quality.\n"
        f"Check every field individually: {fields}.\n"
        "Flag a GAP when an upstream requirement has no corresponding field "
        "content. Flag a CONTRADICTION when fields conflict.\n"
        'Answer with ONLY JSON: {"gaps": [], "contradictions": []}.\n\n'
        f"HAND-OFF:\n{json.dumps(handoff, ensure_ascii=False)[:6000]}\n\n"
        f"UPSTREAM:\n{json.dumps(upstream or {}, ensure_ascii=False)[:6000]}"
    )
    try:
        r = subprocess.run(shlex.split(cmd) + [prompt],
                           capture_output=True, text=True, timeout=120)
        a, b = r.stdout.find("{"), r.stdout.rfind("}")
        verdict = json.loads(r.stdout[a:b + 1]) if a != -1 and b != -1 else None
        if not isinstance(verdict, dict):
            raise ValueError("no JSON object in verifier output")
    except Exception as exc:
        return [], [f"verifier unavailable ({type(exc).__name__}) — degraded "
                    f"to deterministic floor (control arm); pipeline unaffected"]
    findings = ([f"GAP (cross-model): {g}" for g in verdict.get("gaps") or []] +
                [f"CONTRADICTION (cross-model): {c}"
                 for c in verdict.get("contradictions") or []])
    return findings, [f"verifier ran: {len(findings)} finding(s)"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("handoff", help="hand-off artifact JSON (execution prompt, spec, …)")
    ap.add_argument("--spec", required=True, help="handoff-spec.json")
    ap.add_argument("--upstream", help="upstream source JSON (blueprint) for the cross-model layer")
    ap.add_argument("--verifier-cmd", help="external verifier CLI; prompt appended as last arg; fails soft")
    args = ap.parse_args()

    handoff = load(args.handoff, "handoff")
    spec = load(args.spec, "spec")
    upstream = load(args.upstream, "upstream") if args.upstream else None

    findings = deterministic_floor(handoff, spec)
    notes: list[str] = []
    if args.verifier_cmd:
        more, notes = cross_model_layer(handoff, upstream, args.verifier_cmd, spec)
        findings += more

    for n in notes:
        print(f"  [note] {n}")
    if findings:
        print(f"\n{len(findings)} finding(s):", file=sys.stderr)
        for f in findings:
            print(f"  ✗ {f}", file=sys.stderr)
        return 1
    print("✅ hand-off is complete and consistent"
          + ("" if args.verifier_cmd else " (deterministic floor only)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
