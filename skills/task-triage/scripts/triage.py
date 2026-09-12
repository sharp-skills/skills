#!/usr/bin/env python3
"""Task triage / crew scoping for multi-agent pipelines.

Given a goal, produce a *scope*: the smallest set of agents the dispatcher
may offer for this task. Hybrid by design:

  * an optional external classifier (any CLI printing JSON) proposes a
    template — and fails SOFT to keyword rules;
  * deterministic FORCE rules add compliance-critical groups regardless of
    what the classifier said;
  * every route keeps a mandatory spine; unknown tasks get the full crew;
  * `--check-registry` proves the scoped event chain can still reach a
    terminal event (anti-stall).

Config is data (triage-config.json): spines, groups, templates, keyword and
force rules. Stdlib only.

Exit codes: 0 = scope printed (and reachable, if checked);
            2 = config/registry error or the scope cannot reach a terminal.
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path


def die(msg: str) -> "NoReturn":
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(2)


def load_json(path: str, what: str) -> dict:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        die(f"cannot read {what} {path}: {exc}")


def classify_external(goal: str, cmd: str, templates: dict) -> dict | None:
    """Ask an external classifier CLI; fail SOFT (None) on any problem."""
    prompt = (
        "Classify this task for crew routing. Respond with ONLY a JSON object "
        f'{{"template": one of {sorted(templates)}, "extra_groups": []}}. '
        "Pick the SMALLEST crew that can deliver it. Task:\n" + goal[:1500]
    )
    try:
        r = subprocess.run(shlex.split(cmd) + [prompt],
                           capture_output=True, text=True, timeout=60)
        a, b = r.stdout.find("{"), r.stdout.rfind("}")
        if a != -1 and b != -1:
            d = json.loads(r.stdout[a:b + 1])
            if d.get("template") in templates:
                return d
    except Exception:
        pass
    return None


def keyword_template(goal: str, cfg: dict) -> str:
    g = goal.lower()
    for template, pattern in cfg.get("template_keywords") or []:
        try:
            if re.search(pattern, g, re.IGNORECASE):
                return template
        except re.error:
            continue
    return str(cfg.get("default_template", ""))


def resolve(goal: str, cfg: dict, llm_cmd: str | None = None) -> dict:
    templates: dict = cfg.get("templates") or {}
    groups: dict = cfg.get("groups") or {}
    if not templates or "core" not in cfg:
        die("config needs 'core' (mandatory spine) and 'templates'")

    llm = classify_external(goal, llm_cmd, templates) if llm_cmd else None
    template = (llm or {}).get("template") or keyword_template(goal, cfg)
    if template not in templates:
        die(f"default_template {template!r} is not in templates")
    source = "llm" if llm else "rules"

    # Short routes replace the spine entirely (e.g. pure content needs no
    # engineering chain) — they carry their own core.
    short = (cfg.get("short_routes") or {}).get(template)
    if short:
        scope = set(short.get("core") or [])
        for name, pattern in (short.get("extras") or {}).items():
            if re.search(pattern, goal, re.IGNORECASE):
                scope |= set((groups.get(name) or []))
        forced: list[str] = []
    else:
        selected = set(templates.get(template) or [])
        selected |= set((llm or {}).get("extra_groups") or []) & set(groups)
        forced = []
        # Rule guards TRUMP the classifier: compliance groups cannot be
        # under-scoped by a cheap model's optimism.
        for grp, pattern in cfg.get("force_rules") or []:
            try:
                if re.search(pattern, goal, re.IGNORECASE) and grp in groups:
                    if grp not in selected:
                        forced.append(grp)
                    selected.add(grp)
            except re.error:
                continue
        scope = set(cfg["core"])
        for grp in selected:
            scope |= set(groups.get(grp) or [])

    return {"scope": sorted(scope), "template": template, "forced": forced,
            "source": source, "n_agents": len(scope)}


def check_reachable(scope: set[str], registry: dict, cfg: dict) -> list[str]:
    """Anti-stall proof: within the scope, walk entry events through the
    pub/sub graph and require a terminal event to be reachable. Every stall
    observed in testing was exactly a missing spine agent — this check turns
    that failure class from a silent hang into a CI error."""
    agents_path = str(cfg.get("registry_agents_path", "agents"))
    agents = registry.get(agents_path, registry) if agents_path else registry
    if not isinstance(agents, dict):
        die("registry agents did not resolve to an object")
    unknown = [a for a in scope if a not in agents]
    problems = [f"scope agent {a!r} is not in the registry" for a in unknown]

    entry = set(registry.get("entry_events") or [])
    terminal = set(registry.get("terminal_events") or [])
    if not entry or not terminal:
        problems.append("registry needs entry_events and terminal_events for the reachability proof")
        return problems

    available = set(entry)
    fired = True
    while fired:
        fired = False
        for aid in scope:
            a = agents.get(aid) or {}
            subs = set(a.get("subscribes_to") or [])
            if (subs & available or "ALL" in subs or "*" in subs):
                pubs = set(a.get("publishes") or [])
                if not pubs <= available:
                    available |= pubs
                    fired = True
    if not (available & terminal):
        problems.append(
            f"scope stalls: no terminal event reachable from {sorted(entry)} "
            f"within the scoped graph — a spine agent is missing")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("goal", help="the task/goal text to triage")
    ap.add_argument("--config", required=True, help="triage-config.json")
    ap.add_argument("--llm-cmd", help="external classifier CLI (gets the prompt as last arg; fails soft)")
    ap.add_argument("--check-registry", help="registry JSON; prove the scope reaches a terminal event")
    args = ap.parse_args()

    cfg = load_json(args.config, "config")
    result = resolve(args.goal, cfg, args.llm_cmd)

    if args.check_registry:
        registry = load_json(args.check_registry, "registry")
        problems = check_reachable(set(result["scope"]), registry, cfg)
        if problems:
            for p in problems:
                print(f"  ✗ {p}", file=sys.stderr)
            return 2
        result["reachability"] = "terminal reachable"

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
