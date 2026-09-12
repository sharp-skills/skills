#!/usr/bin/env python3
"""Runtime status gate for event-routed multi-agent pipelines.

An agent's emitted `status` IS its routing event: a value outside the agent's
registry `publishes` routes nowhere and silently stops the pipeline. This
gate checks one emitted status against the registry and — on rejection —
prints a message that TEACHES the allowed vocabulary, so a retrying model can
converge instead of repeating the invention.

Usable two ways:
  * library:  from status_gate import gate; verdict = gate(...)
  * CLI:      status_gate.py --registry reg.json --agent X --status Y

Exit codes: 0 = status routes (or gate not applicable: exempt observer,
unknown agent, no status), 2 = status would never route (reject).

Config (optional, shares vocabulary with prompt-contracts):
  {"extra_allowed": ["PIPELINE_FAILED"], "allowed_suffixes": ["_SKIPPED"],
   "exempt": ["event_bus"], "registry": {"agents_path": "agents",
   "publishes_key": "publishes"}}

Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_CONFIG = {
    "extra_allowed": ["PIPELINE_FAILED"],
    "allowed_suffixes": ["_SKIPPED"],
    "exempt": [],
    "registry": {"agents_path": "agents", "publishes_key": "publishes", "id_key": "id"},
}


@dataclass
class Verdict:
    ok: bool
    reason: str                     # ALLOWED | EXEMPT_OBSERVER | UNKNOWN_AGENT | NO_STATUS | REJECTED
    allowed: frozenset[str] = field(default_factory=frozenset)

    def message(self, agent: str, status: str | None) -> str:
        if self.ok:
            return f"{agent}: status {status!r} -> {self.reason}"
        vocab = ", ".join(sorted(self.allowed)) or "(none)"
        return (f"{agent}: status {status!r} REJECTED — it never routes. "
                f"This agent may emit: {vocab}. Re-emit the output with a "
                f"status from that vocabulary; do not invent new ones.")


def dig(doc: dict, dotted: str) -> object:
    node = doc
    for key in filter(None, dotted.split(".")):
        if not isinstance(node, dict) or key not in node:
            raise KeyError(f"registry path {dotted!r}: key {key!r} not found")
        node = node[key]
    return node


def load_registry(path: str | Path, cfg: dict) -> dict:
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    reg = cfg.get("registry", {})
    agents = dig(doc, str(reg.get("agents_path", "agents")))
    # Accept both shapes so the gate reads the same registry the bus derives from:
    #   dict  — {agent_id: {publishes: [...]}}                      (status-gates native)
    #   list  — [{id: agent_id, publishes: [...]}, ...]             (registry-ssot canonical)
    if isinstance(agents, list):
        id_key = str(reg.get("id_key", "id"))
        agents = {a[id_key]: a for a in agents
                  if isinstance(a, dict) and id_key in a}
    if not isinstance(agents, dict):
        raise ValueError("agents_path did not resolve to an object or a list of agents with an id")
    return agents


def gate(agents: dict, agent_id: str, status: str | None, cfg: dict | None = None) -> Verdict:
    """The gate. Deterministic; derives everything from the registry + config."""
    cfg = {**DEFAULT_CONFIG, **(cfg or {})}
    publishes_key = str(cfg.get("registry", {}).get("publishes_key", "publishes"))

    # Rule 4: observers are exempt BY NAME — their status is an ack, not a bus event.
    if agent_id in set(cfg.get("exempt") or []):
        return Verdict(True, "EXEMPT_OBSERVER")

    entry = agents.get(agent_id)
    # Rule 5: unknown agent = registration problem, not a status problem — fail open.
    if entry is None:
        return Verdict(True, "UNKNOWN_AGENT")
    if status is None:
        return Verdict(True, "NO_STATUS")

    # Rule 1: allowed set is DERIVED — publishes + skip forms + shared terminals.
    allowed = frozenset(entry.get(publishes_key) or []) | frozenset(cfg.get("extra_allowed") or [])
    if status in allowed or any(status.endswith(sfx) for sfx in cfg.get("allowed_suffixes") or []):
        return Verdict(True, "ALLOWED", allowed)
    return Verdict(False, "REJECTED", allowed)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--registry", required=True, help="registry JSON (the routing source of truth)")
    ap.add_argument("--agent", required=True, help="agent id as it appears in the registry")
    ap.add_argument("--status", help="emitted status to check (omit to model 'no status emitted')")
    ap.add_argument("--config", help="optional gate config JSON (exempt list, extra_allowed, suffixes)")
    args = ap.parse_args()

    cfg = dict(DEFAULT_CONFIG)
    if args.config:
        try:
            cfg.update(json.loads(Path(args.config).read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"ERROR: cannot read config: {exc}", file=sys.stderr)
            return 2
    try:
        agents = load_registry(args.registry, cfg)
    except (OSError, json.JSONDecodeError, KeyError, ValueError) as exc:
        print(f"ERROR: cannot read registry: {exc}", file=sys.stderr)
        return 2

    verdict = gate(agents, args.agent, args.status, cfg)
    stream = sys.stdout if verdict.ok else sys.stderr
    print(verdict.message(args.agent, args.status), file=stream)
    return 0 if verdict.ok else 2


if __name__ == "__main__":
    sys.exit(main())
