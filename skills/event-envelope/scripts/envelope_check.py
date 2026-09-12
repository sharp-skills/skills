#!/usr/bin/env python3
"""Validate the event envelope — the wire contract that lets one control plane
re-enter identically no matter which runtime an agent ran on.

Two independent checks, either or both:

  1. DRIFT (--runtimes-source): the schema's `runtime` enum MUST equal the
     canonical runtime set the dispatcher routes on. If a new runtime is added
     to the dispatcher but not the envelope schema (or vice versa), events from
     that runtime validate in one place and are rejected in the other — the
     single worst envelope bug, because it only bites the runtime you added
     last. This check makes the two enums a provable pair.

  2. WIRE (--events): every envelope in a JSONL stream carries the required
     correlation fields, a known runtime, a known pipeline_mode (if present),
     and an in-range confidence_score (if present). Validated with stdlib only
     so the exact same rules run under every runtime — no jsonschema dependency
     that one runtime might have and another might not.

Schema shape (draft-07 subset this reads):
  properties.runtime.enum        -> allowed runtimes
  properties.pipeline_mode.enum  -> allowed run modes (optional field)
  required                       -> required correlation fields
  properties.confidence_score    -> minimum/maximum (nullable)

Exit codes: 0 = contract holds, 1 = violations, 2 = bad input. Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def die(msg: str) -> "NoReturn":
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(2)


def load_json(path: str, what: str) -> dict:
    try:
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        die(f"cannot read {what} {path}: {exc}")
    if not isinstance(doc, dict):
        die(f"{what} must be a JSON object: {path}")
    return doc


def read_lines(path: str) -> list[str]:
    try:
        return Path(path).read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        die(f"cannot read events {path}: {exc}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--schema", required=True, help="envelope JSON schema")
    ap.add_argument("--runtimes-source", help="canonical runtime enum, one id per line (drift check)")
    ap.add_argument("--events", help="JSONL of envelopes to validate against the schema")
    args = ap.parse_args()

    if not args.runtimes_source and not args.events:
        die("nothing to check: pass --runtimes-source and/or --events")

    schema = load_json(args.schema, "schema")
    props = schema.get("properties")
    if not isinstance(props, dict):
        die("schema has no 'properties' object")

    required = schema.get("required") or []
    rt_prop = props.get("runtime") or {}
    schema_runtimes = set(rt_prop.get("enum") or [])
    if not schema_runtimes:
        die("schema.properties.runtime.enum is empty — the wire contract has no runtimes")
    mode_prop = props.get("pipeline_mode") or {}
    schema_modes = set(mode_prop.get("enum") or [])
    score_prop = props.get("confidence_score") or {}
    score_min = score_prop.get("minimum", 0)
    score_max = score_prop.get("maximum", 100)

    violations: list[str] = []

    # 1. drift between the schema enum and the dispatcher's runtime set
    if args.runtimes_source:
        source = {
            ln.strip()
            for ln in read_lines(args.runtimes_source)
            if ln.strip() and not ln.lstrip().startswith("#")
        }
        if not source:
            die("runtimes-source is empty")
        missing = source - schema_runtimes
        extra = schema_runtimes - source
        for r in sorted(missing):
            violations.append(
                f"runtime {r!r} routes in the dispatcher but is NOT in the "
                f"envelope schema enum — its events will be rejected on the wire")
        for r in sorted(extra):
            violations.append(
                f"runtime {r!r} is in the envelope schema but the dispatcher "
                f"doesn't route it — dead enum value, or a rename drifted")

    # 2. per-envelope wire validation
    checked = 0
    if args.events:
        for i, line in enumerate(read_lines(args.events), 1):
            line = line.strip()
            if not line:
                continue
            checked += 1
            try:
                env = json.loads(line)
            except json.JSONDecodeError as exc:
                violations.append(f"line {i}: not valid JSON ({exc})")
                continue
            if not isinstance(env, dict):
                violations.append(f"line {i}: envelope is not an object")
                continue
            for key in required:
                v = env.get(key)
                if not (isinstance(v, str) and v.strip()):
                    violations.append(f"line {i}: missing/empty required field {key!r}")
            rt = env.get("runtime")
            if rt is not None and rt not in schema_runtimes:
                violations.append(
                    f"line {i}: runtime {rt!r} not in {sorted(schema_runtimes)}")
            mode = env.get("pipeline_mode")
            if mode is not None and schema_modes and mode not in schema_modes:
                violations.append(
                    f"line {i}: pipeline_mode {mode!r} not in {sorted(schema_modes)}")
            score = env.get("confidence_score")
            if score is not None and not (
                isinstance(score, (int, float)) and not isinstance(score, bool)
                and score_min <= score <= score_max
            ):
                violations.append(
                    f"line {i}: confidence_score must be {score_min}-{score_max} or null")

    print(f"Checked {len(schema_runtimes)} runtime(s), {checked} envelope(s).")
    if violations:
        print(f"\n{len(violations)} violation(s):", file=sys.stderr)
        for v in violations:
            print(f"  ✗ {v}", file=sys.stderr)
        return 1
    print("✅ Envelope contract holds: runtime enum agrees, envelopes well-formed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
