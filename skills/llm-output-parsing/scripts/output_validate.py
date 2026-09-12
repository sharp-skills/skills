#!/usr/bin/env python3
"""Extract and validate an LLM's structured output before a consumer uses it.

A model asked for JSON rarely returns *only* JSON. It wraps it in ```json
fences, prefaces it with "Here is the result:", leaves a trailing comma, or
returns prose instead. A downstream agent that does `json.loads(raw)` crashes on
all of these. This check does the deterministic part — locate the JSON, apply
safe repairs, validate against a schema — and tells you cleanly whether the
output is usable or a re-ask is needed.

Pipeline:

  1. EXTRACT — pull the JSON out of a fenced block, or find the outermost
     balanced {...}/[...] in surrounding prose.
  2. REPAIR  — apply only *safe, deterministic* fixes (strip trailing commas).
     Never guess values; repairing content is the model's job, not this check's.
  3. PARSE   — json.loads the candidate.
  4. VALIDATE— required fields present, types match, enums and numeric bounds
     hold.

What it does NOT do: rewrite the content, fill missing fields, or call a model.
On unrepairable/invalid output it exits 1 — the caller's cue to re-ask with the
error as feedback (bounded retry; see the reference).

Schema shape (out.schema.json): a JSON-Schema subset —
  {"required": ["action"],
   "properties": {"action": {"type": "string", "enum": ["approve", "reject"]},
                  "confidence": {"type": "number", "minimum": 0, "maximum": 100}}}

Exit codes: 0 = valid, 1 = unextractable/invalid (re-ask), 2 = bad input.
Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

TYPES = {
    "string": str, "object": dict, "array": list, "boolean": bool,
}


def die(msg: str) -> "NoReturn":
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(2)


def extract(raw: str) -> "str | None":
    # 1. fenced block ```json ... ``` or ``` ... ```
    m = re.search(r"```(?:json)?\s*(.+?)```", raw, re.S | re.I)
    if m:
        return m.group(1).strip()
    # 2. outermost balanced brackets in prose
    start = None
    for i, ch in enumerate(raw):
        if ch in "{[":
            start = i
            break
    if start is None:
        return None
    open_ch = raw[start]
    close_ch = "}" if open_ch == "{" else "]"
    depth = 0
    for j in range(start, len(raw)):
        if raw[j] == open_ch:
            depth += 1
        elif raw[j] == close_ch:
            depth -= 1
            if depth == 0:
                return raw[start:j + 1]
    return None


def repair(candidate: str) -> str:
    # only safe, deterministic: remove trailing commas before } or ]
    return re.sub(r",(\s*[}\]])", r"\1", candidate)


def type_ok(value, jtype: str) -> bool:
    if jtype in ("number", "integer"):
        if isinstance(value, bool):
            return False
        return isinstance(value, int) if jtype == "integer" else isinstance(value, (int, float))
    py = TYPES.get(jtype)
    return isinstance(value, py) if py else True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--schema", required=True, help="output JSON schema (subset)")
    ap.add_argument("--output", required=True, help="raw LLM output text")
    args = ap.parse_args()

    try:
        schema = json.loads(Path(args.schema).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        die(f"cannot read schema {args.schema}: {exc}")
    if not isinstance(schema, dict):
        die("schema must be a JSON object")
    try:
        raw = Path(args.output).read_text(encoding="utf-8")
    except OSError as exc:
        die(f"cannot read output {args.output}: {exc}")

    problems: list[str] = []

    candidate = extract(raw)
    if candidate is None:
        print("✗ no JSON found in the output — the model returned prose; re-ask.", file=sys.stderr)
        return 1
    try:
        doc = json.loads(candidate)
    except json.JSONDecodeError:
        try:
            doc = json.loads(repair(candidate))
        except json.JSONDecodeError as exc:
            print(f"✗ extracted text is not valid JSON even after safe repair: {exc}", file=sys.stderr)
            return 1

    if not isinstance(doc, dict):
        print("✗ top-level output is not an object", file=sys.stderr)
        return 1

    props = schema.get("properties") or {}
    for req in schema.get("required") or []:
        if req not in doc:
            problems.append(f"missing required field {req!r}")
    for key, spec in props.items():
        if key not in doc:
            continue
        val = doc[key]
        jtype = spec.get("type")
        if jtype and not type_ok(val, jtype):
            problems.append(f"field {key!r} should be {jtype}, got {type(val).__name__}")
            continue
        enum = spec.get("enum")
        if enum is not None and val not in enum:
            problems.append(f"field {key!r} = {val!r} not in enum {enum}")
        if isinstance(val, (int, float)) and not isinstance(val, bool):
            if "minimum" in spec and val < spec["minimum"]:
                problems.append(f"field {key!r} = {val} below minimum {spec['minimum']}")
            if "maximum" in spec and val > spec["maximum"]:
                problems.append(f"field {key!r} = {val} above maximum {spec['maximum']}")

    if problems:
        print(f"✗ output extracted and parsed but invalid ({len(problems)}):", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    print("✅ output extracted, repaired if needed, and valid against the schema.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
