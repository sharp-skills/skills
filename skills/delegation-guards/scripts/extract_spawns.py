#!/usr/bin/env python3
"""Build a delegation tree (spawns.json) from an observability-tracing trace.

The delegation checker audits a tree of `{id, parent, agent}` nodes — but in a
real system you don't hand-write that tree, you *have* it already: every span in
the run's trace carries a `parent` link, and the span nesting IS the delegation
structure. This extractor reconstructs the tree the checker needs from the trace
the run already recorded, so the audit runs on the real shape, not a manifest
you transcribed by hand (and could transcribe wrong).

Only agent-turn spans are treated as delegation nodes; tool calls are not
spawns, so their spans are skipped by default (`--kinds` overrides). A span seen
more than once (e.g. a tool_call then a step_complete) collapses to one node;
the agent-turn event supplies its `agent`.

  python3 extract_spawns.py trace.jsonl                 # -> spawns.json on stdout
  python3 extract_spawns.py trace.jsonl --out spawns.json
  python3 extract_spawns.py trace.jsonl | \\
    python3 delegation_check.py --tree /dev/stdin --policy policy.json

Exit codes: 0 = tree written, 2 = bad input. Stdlib only, offline.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SPAWN_KINDS = {"trace_start", "step_complete"}


def die(msg: str) -> "NoReturn":
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(2)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("trace", help="observability-tracing JSONL (one event per line)")
    ap.add_argument("--out", help="write the tree here (default: stdout)")
    ap.add_argument("--kinds", help="comma-separated event kinds to treat as spawn nodes",
                    default=",".join(sorted(SPAWN_KINDS)))
    args = ap.parse_args()

    path = Path(args.trace)
    if not path.is_file():
        die(f"trace not found: {path}")
    kinds = {k.strip() for k in args.kinds.split(",") if k.strip()}

    # span id -> node; first agent-turn event for a span wins its agent/parent.
    nodes: dict[str, dict] = {}
    order: list[str] = []
    seen_any = False
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        raw = raw.strip()
        if not raw:
            continue
        try:
            ev = json.loads(raw)
        except json.JSONDecodeError as exc:
            print(f"  [warn] line {lineno} malformed JSON, skipped: {exc}", file=sys.stderr)
            continue
        seen_any = True
        if ev.get("kind") not in kinds:
            continue
        span = ev.get("span")
        if not span:
            continue
        if span not in nodes:
            nodes[span] = {"id": span, "parent": ev.get("parent"), "agent": ev.get("agent")}
            order.append(span)

    if not seen_any:
        die(f"no events parsed from {path}")
    if not nodes:
        die(f"no spawn nodes found (looked for kinds {sorted(kinds)}) — is this a trace?")

    tree = {"nodes": [nodes[s] for s in order]}
    text = json.dumps(tree, indent=2) + "\n"
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"wrote {len(order)} node(s) -> {args.out}", file=sys.stderr)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
