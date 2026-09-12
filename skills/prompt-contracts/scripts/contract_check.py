#!/usr/bin/env python3
"""Static contract check for multi-agent pipelines.

Verifies that three layers of a multi-agent system agree on output statuses:

  1. registry  — which events each agent may publish (the source of truth)
  2. schemas   — which `status` values each agent's output schema accepts
  3. prompts   — which status literals each agent's prompt teaches (incl. examples)

Rule: for every non-exempt agent, every status a schema or prompt offers must be
a registry-published event of that agent, an allowed suffix form (e.g. *_SKIPPED),
or a globally allowed value (e.g. PIPELINE_FAILED).

Stdlib only. Exit codes: 0 = contract holds, 1 = violations, 2 = bad input.

Usage:
  contract_check.py --config contract-config.json
  contract_check.py --config contract-config.json --agent BA   # check one agent

Config shape: see references/config.md next to this skill.
"""

from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from pathlib import Path

# Status literals a prompt "teaches":  "status": "X"  |  status: X  |  status = "X"
# Only UPPER_SNAKE tokens count — prose like `status: pending review` is ignored.
PROMPT_STATUS_RE = re.compile(
    r"""["']?status["']?\s*[:=]\s*["']?([A-Z][A-Z0-9_]{2,})["']?"""
)


def fail_input(msg: str) -> "NoReturn":
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(2)


def load_json(path: Path, what: str) -> dict:
    if not path.exists():
        fail_input(f"{what} not found: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        fail_input(f"{what} is not valid JSON ({path}): {e}")


def dig(doc: dict, dotted: str) -> object:
    """Resolve 'a.b.c' inside a JSON document; empty string = whole document."""
    node = doc
    for key in filter(None, dotted.split(".")):
        if not isinstance(node, dict) or key not in node:
            fail_input(f"registry path {dotted!r}: key {key!r} not found")
        node = node[key]
    return node


def collect_status_enums(node: object, acc: list[str]) -> list[str]:
    """Collect every status enum/const, recursing through oneOf/anyOf/allOf.

    Recursion is mandatory: composed variants are exactly where forbidden
    statuses hide from top-level-only checks (see references/failure-catalog.md).
    """
    if not isinstance(node, dict):
        return acc
    st = (node.get("properties") or {}).get("status") or {}
    if isinstance(st, dict):
        for v in st.get("enum") or ([st["const"]] if "const" in st else []):
            if isinstance(v, str):
                acc.append(v)
    for key in ("oneOf", "anyOf", "allOf"):
        for sub in node.get(key) or []:
            collect_status_enums(sub, acc)
    # `definitions`/`$defs` referenced variants
    for defs_key in ("definitions", "$defs"):
        for sub in (node.get(defs_key) or {}).values():
            collect_status_enums(sub, acc)
    return acc


def allowed_for(agent: str, publishes: list[str], cfg: dict) -> set[str]:
    return set(publishes) | set(cfg.get("extra_allowed") or [])


def is_allowed(value: str, allowed: set[str], cfg: dict) -> bool:
    if value in allowed:
        return True
    return any(value.endswith(sfx) for sfx in cfg.get("allowed_suffixes") or [])


def expand_files(base: Path, patterns: list[str] | str, what: str,
                 agent: str, errors: list[str]) -> list[Path]:
    if isinstance(patterns, str):
        patterns = [patterns]
    out: list[Path] = []
    for pat in patterns:
        hits = sorted(glob.glob(str(base / pat)))
        if not hits:
            errors.append(f"{agent}: {what} pattern matched nothing: {pat}")
        out.extend(Path(h) for h in hits)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", required=True, help="path to contract-config.json")
    ap.add_argument("--agent", help="check a single agent id from the config map")
    args = ap.parse_args()

    cfg_path = Path(args.config)
    cfg = load_json(cfg_path, "config")
    root = cfg_path.parent / cfg.get("root", ".")

    registry = load_json(root / cfg["registry"]["file"], "registry")
    agents_node = dig(registry, cfg["registry"].get("agents_path", ""))
    if not isinstance(agents_node, dict):
        fail_input("registry agents_path did not resolve to an object")
    publishes_key = cfg["registry"].get("publishes_key", "publishes")

    agent_map: dict = cfg.get("agents") or {}
    if not agent_map:
        fail_input("config has no 'agents' map — wiring must be explicit "
                   "(implicit derivation is a fail-open hole; see failure catalog)")
    if args.agent:
        if args.agent not in agent_map:
            fail_input(f"--agent {args.agent}: not in config agents map")
        agent_map = {args.agent: agent_map[args.agent]}

    exempt = set(cfg.get("exempt") or [])
    violations: list[str] = []
    errors: list[str] = []
    checked_schemas = checked_prompts = 0

    for agent, wiring in sorted(agent_map.items()):
        if agent in exempt:
            print(f"  {agent}: exempt (named observer/ack agent)")
            continue
        entry = agents_node.get(wiring.get("registry_id", agent))
        if entry is None:
            errors.append(f"{agent}: registry has no entry "
                          f"{wiring.get('registry_id', agent)!r} — explicit wiring "
                          f"must fail loudly, fix the config")
            continue
        allowed = allowed_for(agent, entry.get(publishes_key) or [], cfg)

        # 1. schema enums (recursive)
        for sp in expand_files(root, wiring.get("schema") or [], "schema",
                               agent, errors):
            doc = load_json(sp, f"{agent} schema")
            enum = collect_status_enums(doc, [])
            checked_schemas += 1
            for v in sorted(set(enum)):
                if not is_allowed(v, allowed, cfg):
                    violations.append(
                        f"{agent}: schema {sp.name} offers status {v!r} the "
                        f"registry never publishes — the status IS the routing "
                        f"event, the dispatcher would reject it every time. "
                        f"Align the enum to {sorted(allowed)} or drop it.")

        # 2. prompt exemplars
        for pp in expand_files(root, wiring.get("prompts") or [], "prompt",
                               agent, errors):
            text = pp.read_text(encoding="utf-8", errors="replace")
            checked_prompts += 1
            taught = {m.group(1) for m in PROMPT_STATUS_RE.finditer(text)}
            for v in sorted(taught):
                if not is_allowed(v, allowed, cfg):
                    violations.append(
                        f"{agent}: prompt {pp.name} teaches status {v!r} "
                        f"(likely inside a worked example) that the registry "
                        f"forbids — the model imitates examples over rules.")

    print(f"\nChecked {checked_schemas} schema(s), {checked_prompts} prompt "
          f"file(s) across {len(agent_map)} agent(s); {len(exempt)} exempt.")

    if errors:
        print(f"\n{len(errors)} wiring error(s):", file=sys.stderr)
        for e in errors:
            print(f"  ✗ {e}", file=sys.stderr)
        return 2
    if violations:
        print(f"\n{len(violations)} contract violation(s):", file=sys.stderr)
        for v in violations:
            print(f"  ✗ {v}", file=sys.stderr)
        return 1
    print("✅ Contract holds: registry, schemas, and prompts agree.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
