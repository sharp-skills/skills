#!/usr/bin/env python3
"""Runtime audit for mechanized agents.

Cross-checks the routing registry against a handler manifest so a
runtime="code" flip can't drift out of contract:

  1. every registry agent with runtime "code"/"hybrid" has a manifest handler;
  2. every event a handler may emit is that agent's registry publish-event
     (same-events-out rule — the rest of the pipeline must not notice a flip);
  3. every hybrid handler declares a defer_status, and that status is NOT a
     registry event of any agent (defer is an internal hand-off, not routing);
  4. manifest handlers that point at agents the registry doesn't know fail
     loudly (explicit wiring, never silent skips).

Manifest shape (handlers.json):
  {"agents": {
     "publisher": {"runtime": "code",   "module": "handlers/git.py",
                    "events": ["GITHUB_PR_OPENED", "GITHUB_MERGED"]},
     "cost_gate":   {"runtime": "hybrid", "module": "handlers/cost.py",
                    "events": ["COST_GATE_PASSED", "COST_GATE_BLOCKED"],
                    "defer_status": "ANALYST_REQUIRED"}}}

Registry: agents map with `publishes` and optional `runtime` per agent
(same format as the rest of this bundle).

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


def load(path: str, what: str) -> dict:
    try:
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        die(f"cannot read {what} {path}: {exc}")
    if not isinstance(doc, dict):
        die(f"{what} must be a JSON object: {path}")
    return doc


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--registry", required=True, help="routing registry JSON")
    ap.add_argument("--manifest", required=True, help="handler manifest JSON")
    ap.add_argument("--agents-path", default="agents", help="key of the agents map in both files")
    args = ap.parse_args()

    reg = load(args.registry, "registry")
    man = load(args.manifest, "manifest")
    reg_agents = reg.get(args.agents_path, reg)
    man_agents = man.get(args.agents_path, man)
    if not isinstance(reg_agents, dict) or not isinstance(man_agents, dict):
        die("agents map did not resolve to an object in registry or manifest")

    all_events: set[str] = set()
    for a in reg_agents.values():
        all_events |= set(a.get("publishes") or [])

    violations: list[str] = []

    # 1. registry code/hybrid agents must have handlers
    for aid, entry in sorted(reg_agents.items()):
        runtime = str(entry.get("runtime", "llm"))
        if runtime in ("code", "hybrid") and aid not in man_agents:
            violations.append(
                f"{aid}: registry says runtime={runtime!r} but the manifest has "
                f"no handler — the dispatcher would fan out to nothing")

    for aid, h in sorted(man_agents.items()):
        entry = reg_agents.get(aid)
        # 4. explicit wiring fails loudly
        if entry is None:
            violations.append(
                f"{aid}: manifest handler for an agent the registry doesn't "
                f"know — fix the id or remove the handler (silent skips are "
                f"how unguarded surface is born)")
            continue
        allowed = set(entry.get("publishes") or [])
        runtime = str(h.get("runtime", "code"))

        # 2. same events out
        for ev in h.get("events") or []:
            if ev not in allowed:
                violations.append(
                    f"{aid}: handler may emit {ev!r} which is not in the "
                    f"registry publishes {sorted(allowed)} — a flip must keep "
                    f"the same events out, or every consumer changes too")

        # 3. hybrid defer contract
        if runtime == "hybrid":
            defer = h.get("defer_status")
            if not defer:
                violations.append(
                    f"{aid}: hybrid handler without defer_status — the code "
                    f"path has no declared way to hand ambiguity to the LLM")
            elif defer in all_events:
                violations.append(
                    f"{aid}: defer_status {defer!r} is a registry event — "
                    f"defer is an internal hand-off, not a bus event; routing "
                    f"it doubles the event surface")

    checked = len(man_agents)
    print(f"Checked {checked} handler(s) against {len(reg_agents)} registry agent(s).")
    if violations:
        print(f"\n{len(violations)} violation(s):", file=sys.stderr)
        for v in violations:
            print(f"  ✗ {v}", file=sys.stderr)
        return 1
    print("✅ Mechanization contract holds: handlers, events, and defer statuses agree.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
