#!/usr/bin/env python3
"""Pre-flight validation for LLM-proposed tool calls, before they execute.

A model driving tools produces calls that a human never would: a destructive
command it didn't mean to run twice, a call with a placeholder path it never
filled in, the same fetch fired seven times "to be sure". This check sits
between the model's proposed call and the executor and rejects four classes:

  1. UNKNOWN     — the tool isn't in the allowed schema (typo or hallucinated
                   tool). Never dispatch to a tool you didn't declare.
  2. ARGS        — a required argument is missing/empty, or an argument still
                   holds a placeholder the model never filled (`<path>`, `TODO`,
                   `assumed`, `your-key-here`). Executing on a guessed value is
                   how the wrong file gets written.
  3. DESTRUCTIVE — the tool is marked destructive, or an argument matches a
                   destructive pattern (`rm -rf`, `drop table`, `truncate`),
                   and the call is not explicitly approved. Side-effectful calls
                   need consent, not confidence.
  4. REDUNDANT   — this exact (tool, args) already ran earlier in the batch.
                   The "it seemed to hang, run it again" loop is caught here.

Schema shape (tools.json):
  {"tools": {
     "bash":       {"required": ["command"],
                    "destructive_patterns": ["rm -rf", "\\bdrop\\b", "truncate"]},
     "write_file": {"required": ["path", "content"], "destructive": true},
     "read_file":  {"required": ["path"]}}}

Calls (calls.jsonl), one proposed call per line, in dispatch order:
  {"tool": "bash", "args": {"command": "rm -rf build"}, "approved": true}

Exit codes: 0 = every call is safe to dispatch, 1 = violations, 2 = bad input.
Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

PLACEHOLDER = re.compile(r"(^<.*>$|\bTODO\b|\bFIXME\b|\bassumed\b|\bxxx\b|your-[\w-]*-here|^\s*$)", re.I)


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


def canon(tool: str, args: dict) -> str:
    """Order-independent identity of a call, for dedup."""
    return tool + "\x00" + json.dumps(args, sort_keys=True, ensure_ascii=False)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--schema", required=True, help="allowed tools JSON")
    ap.add_argument("--calls", required=True, help="proposed calls JSONL (dispatch order)")
    args = ap.parse_args()

    schema = load_json(args.schema, "schema")
    tools = schema.get("tools")
    if not isinstance(tools, dict) or not tools:
        die("schema has no non-empty 'tools' object")

    try:
        lines = Path(args.calls).read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        die(f"cannot read calls {args.calls}: {exc}")

    violations: list[str] = []
    seen: set[str] = set()
    checked = 0

    for i, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
        checked += 1
        try:
            call = json.loads(line)
        except json.JSONDecodeError as exc:
            violations.append(f"call {i}: not valid JSON ({exc})")
            continue
        tool = call.get("tool")
        cargs = call.get("args") or {}
        if not isinstance(cargs, dict):
            violations.append(f"call {i}: 'args' must be an object")
            continue

        # 1. unknown tool
        spec = tools.get(tool)
        if spec is None:
            violations.append(
                f"call {i}: tool {tool!r} is not in the allowed schema "
                f"(typo or hallucinated tool)")
            continue

        # 2. args: required present, no placeholders
        for req in spec.get("required") or []:
            if req not in cargs:
                violations.append(f"call {i} [{tool}]: missing required arg {req!r}")
        for k, v in cargs.items():
            if isinstance(v, str) and PLACEHOLDER.search(v):
                violations.append(
                    f"call {i} [{tool}]: arg {k!r} still holds a placeholder "
                    f"{v!r} — the model never filled it in")

        # 3. destructive without approval
        destructive = bool(spec.get("destructive"))
        hit = None
        for pat in spec.get("destructive_patterns") or []:
            for v in cargs.values():
                if isinstance(v, str) and re.search(pat, v, re.I):
                    destructive, hit = True, pat
                    break
            if hit:
                break
        if destructive and call.get("approved") is not True:
            why = f"matches destructive pattern {hit!r}" if hit else "tool is marked destructive"
            violations.append(
                f"call {i} [{tool}]: {why} but is not approved — set "
                f"approved:true only after a human/policy consents")

        # 4. redundant (exact repeat earlier in the batch)
        key = canon(tool, cargs)
        if key in seen:
            violations.append(
                f"call {i} [{tool}]: identical call already issued earlier in "
                f"this batch — redundant (the 'run it again to be sure' loop)")
        seen.add(key)

    print(f"Checked {checked} call(s) against {len(tools)} allowed tool(s).")
    if violations:
        print(f"\n{len(violations)} violation(s):", file=sys.stderr)
        for v in violations:
            print(f"  ✗ {v}", file=sys.stderr)
        return 1
    print("✅ All proposed calls are safe to dispatch: known tools, complete "
          "args, destructive calls approved, no redundant repeats.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
