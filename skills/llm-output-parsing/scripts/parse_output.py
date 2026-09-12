#!/usr/bin/env python3
"""Extract typed signals from free-form model output — and flag ambiguity instead
of silently guessing.

Sometimes you can't get JSON: the producer is a model that answers in prose, or
a component you don't control, or the task is inherently narrative ("...so I'd
lean toward approving, maybe 85% sure"). You still need the decision out of it.
The naive move — regex for the first "approve" — fails silently the moment the
model's *reasoning* mentions "reject" before its *conclusion* says "approve":
you extract the wrong value with full confidence.

This extractor pulls labeled and scannable signals out of prose and, crucially,
reports the outcome honestly per target:

  ok        — exactly one unambiguous value found, valid for its type.
  not_found — no value found; the caller re-asks or uses a default.
  ambiguous — multiple *conflicting* values found (e.g. both "approve" and
              "reject"); the caller must NOT guess — re-ask or escalate.
  invalid   — a value was found but fails its type/enum/bounds.

Extraction per target: prefer an explicit label ("Verdict: approve",
"score = 85", "blocking is yes"); fall back to scanning the whole text.

Spec (spec.json):
  {"targets": [
     {"name": "verdict", "kind": "enum", "values": ["approve", "reject", "revise"]},
     {"name": "score", "kind": "number", "min": 0, "max": 100},
     {"name": "blocking", "kind": "boolean"}]}

Exit codes: 0 = every target extracted cleanly, 1 = not_found/ambiguous/invalid,
2 = bad input. Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

TRUE = {"yes", "true", "y", "1"}
FALSE = {"no", "false", "n", "0"}


def die(msg: str) -> "NoReturn":
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(2)


def labeled_value(text: str, name: str) -> "str | None":
    """Find `name: value`, `name = value`, or `name is value` (first token(s))."""
    m = re.search(rf"\b{re.escape(name)}\b\s*(?::|=|\bis\b)\s*([^\n.,;]+)", text, re.I)
    return m.group(1).strip() if m else None


def extract_enum(text: str, name: str, values: list[str]):
    lab = labeled_value(text, name)
    if lab is not None:
        matched = [v for v in values if re.search(rf"\b{re.escape(v)}\b", lab, re.I)]
        if len(matched) == 1:
            return "ok", matched[0]
        if len(matched) == 0:
            return "invalid", lab
        return "ambiguous", matched
    present = [v for v in values if re.search(rf"\b{re.escape(v)}\b", text, re.I)]
    if len(present) == 1:
        return "ok", present[0]
    if len(present) == 0:
        return "not_found", None
    return "ambiguous", present


def extract_number(text: str, name: str, lo, hi):
    def in_bounds(x):
        return (lo is None or x >= lo) and (hi is None or x <= hi)

    lab = labeled_value(text, name)
    src = lab if lab is not None else text
    nums = [float(n) for n in re.findall(r"-?\d+(?:\.\d+)?", src)]
    nums = [int(n) if n.is_integer() else n for n in nums]
    if lab is not None:
        if not nums:
            return "invalid", lab
        val = nums[0]
        return ("ok", val) if in_bounds(val) else ("invalid", val)
    in_range = sorted({n for n in nums if in_bounds(n)})
    if len(in_range) == 1:
        return "ok", in_range[0]
    if len(in_range) == 0:
        return "not_found", None
    return "ambiguous", in_range


def extract_bool(text: str, name: str):
    lab = labeled_value(text, name)
    src = lab if lab is not None else text
    toks = set(re.findall(r"[A-Za-z01]+", src.lower()))
    t, f = bool(toks & TRUE), bool(toks & FALSE)
    if t and not f:
        return "ok", True
    if f and not t:
        return "ok", False
    if not t and not f:
        return "not_found", None
    return "ambiguous", ["true", "false"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--spec", required=True, help="extraction spec JSON")
    ap.add_argument("--output", required=True, help="raw model output text")
    args = ap.parse_args()

    try:
        spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        die(f"cannot read spec {args.spec}: {exc}")
    targets = spec.get("targets") if isinstance(spec, dict) else None
    if not isinstance(targets, list) or not targets:
        die("spec has no non-empty 'targets' list")
    try:
        text = Path(args.output).read_text(encoding="utf-8")
    except OSError as exc:
        die(f"cannot read output {args.output}: {exc}")

    problems: list[str] = []
    for t in targets:
        name = t.get("name")
        kind = t.get("kind")
        if kind == "enum":
            status, val = extract_enum(text, name, t.get("values") or [])
        elif kind == "number":
            status, val = extract_number(text, name, t.get("min"), t.get("max"))
        elif kind == "boolean":
            status, val = extract_bool(text, name)
        else:
            die(f"target {name!r} has unknown kind {kind!r}")
        if status == "ok":
            print(f"  {name} = {val!r}")
        else:
            problems.append(f"{name}: {status} ({val!r}) — do not guess; re-ask or escalate"
                            if status == "ambiguous" else f"{name}: {status} ({val!r})")

    if problems:
        print(f"\n{len(problems)} unresolved target(s):", file=sys.stderr)
        for p in problems:
            print(f"  ✗ {p}", file=sys.stderr)
        return 1
    print("✅ Every target extracted cleanly and unambiguously.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
