#!/usr/bin/env python3
"""Validate a multi-agent registry JSON file for wiring consistency."""

import argparse
import json
import sys

WILDCARD_TOKENS = {"ALL", "*"}


def _is_wildcard(subscribes_to):
    return bool(set(subscribes_to) & WILDCARD_TOKENS)


def validate(registry_path):
    with open(registry_path) as f:
        data = json.load(f)

    agents = data.get("agents", [])
    terminal_events = set(data.get("terminal_events", []))
    entry_events = set(data.get("entry_events", []))
    bus_derives = data.get("bus_derives_from_registry", False)
    bus_graph = data.get("bus_graph", {})

    errors = []
    warnings = []

    # Pre-compute sets used across checks
    all_published = set()
    for agent in agents:
        all_published.update(agent.get("publishes", []))

    # Entry events count as "published" for orphan checks (externally injected)
    effectively_published = all_published | entry_events

    has_wildcard_agent = any(
        _is_wildcard(a.get("subscribes_to", [])) for a in agents
    )

    all_explicit_subscribed = set()
    for agent in agents:
        subs = agent.get("subscribes_to", [])
        if not _is_wildcard(subs):
            all_explicit_subscribed.update(subs)

    # ── Check 1: Orphan subscriptions ────────────────────────────────────────
    for agent in agents:
        subs = agent.get("subscribes_to", [])
        if _is_wildcard(subs):
            continue  # wildcard agents are never orphaned
        for event in subs:
            if event not in effectively_published:
                errors.append(
                    f"ERROR  orphan subscription: agent '{agent['id']}' subscribes to"
                    f" '{event}' but no agent publishes it (and it is not an entry_event)"
                )

    # ── Check 2: Dead-end publishes ───────────────────────────────────────────
    # Wildcards suppress all dead-end warnings — they cover every event.
    if not has_wildcard_agent:
        for agent in agents:
            for event in agent.get("publishes", []):
                if event in terminal_events:
                    continue  # terminal events are end-states by design
                if event not in all_explicit_subscribed:
                    warnings.append(
                        f"WARN   dead-end publish: agent '{agent['id']}' publishes"
                        f" '{event}' but no agent subscribes to it"
                    )

    # ── Check 3: Bus graph vs registry ────────────────────────────────────────
    if bus_derives:
        # Collect all known events (subscriptions + publishes + entry + terminal)
        all_known_events = set(all_explicit_subscribed) | all_published | entry_events | terminal_events

        # Derive expected bus graph: per event, sorted list of explicit subscribers
        derived = {}
        for event in all_known_events:
            subscribers = sorted(
                a["id"]
                for a in agents
                if not _is_wildcard(a.get("subscribes_to", []))
                and event in a.get("subscribes_to", [])
            )
            derived[event] = subscribers

        # If bus_graph explicitly models wildcards with an ALL/* key, include it
        # in the derived graph so the comparison covers it.
        bus_wildcard_keys = WILDCARD_TOKENS & set(bus_graph.keys())
        if bus_wildcard_keys:
            wildcard_agent_ids = sorted(
                a["id"]
                for a in agents
                if _is_wildcard(a.get("subscribes_to", []))
            )
            for wk in bus_wildcard_keys:
                derived[wk] = wildcard_agent_ids

        snapshot_keys = set(bus_graph.keys())
        derived_keys = set(derived.keys())

        for event in sorted(derived_keys - snapshot_keys):
            errors.append(
                f"ERROR  bus/registry mismatch: event '{event}' is known to"
                f" registry but missing from bus_graph"
            )
        for event in sorted(snapshot_keys - derived_keys):
            errors.append(
                f"ERROR  bus/registry mismatch: event '{event}' is in bus_graph"
                f" but not known to registry"
            )
        for event in sorted(derived_keys & snapshot_keys):
            expected = derived[event]
            actual = sorted(bus_graph[event])
            if expected != actual:
                errors.append(
                    f"ERROR  bus/registry mismatch: event '{event}':"
                    f" registry says {expected}, bus_graph says {actual}"
                )

    return errors, warnings


def main():
    parser = argparse.ArgumentParser(
        prog="validate_registry.py",
        description="Validate a multi-agent registry JSON file for wiring consistency.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
EXIT CODES
  0   No errors. Warnings (dead-end publishes) may be printed but are not blocking.
  1   One or more ERROR conditions detected.

CHECKS
  orphan subscription
      An agent subscribes to an event that no agent publishes and the event is
      not listed in entry_events.
      → ERROR / exit 1

  dead-end publish
      An agent publishes an event that no agent explicitly subscribes to, the
      event is not in terminal_events, and no wildcard subscriber (ALL/*) exists.
      → WARN / exit 0

  bus/registry mismatch
      bus_derives_from_registry is true and bus_graph does not match the routing
      derived from subscribes_to fields.
      → ERROR / exit 1

WILDCARD SUBSCRIBERS (ALL / *)
  Agents with subscribes_to: ["ALL"] or ["*"] are never flagged as orphans
  and suppress all dead-end publish warnings (they cover every event).

  For bus_graph comparison, wildcard agents are NOT expanded into per-event
  entries unless bus_graph explicitly contains an "ALL" or "*" key. In that
  case the value must equal the sorted list of wildcard agent IDs.

ENTRY EVENTS
  Events in entry_events are treated as externally published. Agents that
  subscribe to them are never flagged as orphan subscribers.

TERMINAL EVENTS
  Events in terminal_events may have no subscribers by design. No dead-end
  WARN is issued for them.

EXAMPLES
  python scripts/validate_registry.py registry.json
  python scripts/validate_registry.py --help
""",
    )
    parser.add_argument("registry", help="Path to the registry JSON file")
    args = parser.parse_args()

    try:
        errors, warnings = validate(args.registry)
    except FileNotFoundError:
        print(f"ERROR  file not found: {args.registry}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as exc:
        print(f"ERROR  invalid JSON: {exc}", file=sys.stderr)
        sys.exit(1)

    for line in warnings:
        print(line)
    for line in errors:
        print(line)

    if not errors and not warnings:
        print("OK     registry is valid")
    elif not errors:
        print("OK     no errors (warnings above)")

    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
