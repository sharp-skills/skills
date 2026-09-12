# Validation Reference

`scripts/validate_registry.py` is a stdlib-only Python script that checks a registry JSON file for three classes of wiring error. Run it locally, in CI, or as a session-start hook.

## Quick start

```bash
python scripts/validate_registry.py registry.json
```

## Exit codes

| Code | Meaning |
|---|---|
| `0` | No errors. Warnings may appear (dead-end publishes) but are not blocking. |
| `1` | One or more ERROR conditions found (orphan subscriptions or bus/registry mismatch). |

## Checks

### Orphan subscription — ERROR / exit 1

An agent subscribes to an event that is never published by any other agent and is not listed in `entry_events`.

Common causes: typo in event name, event renamed in publisher but not subscriber, dead code left behind.

### Dead-end publish — WARN / exit 0

An agent publishes an event that no agent explicitly subscribes to, the event is not in `terminal_events`, and no wildcard subscriber (`ALL`/`*`) exists.

Wildcards suppress this warning because they receive every event on the bus — no event is ever truly dead-ended when a wildcard agent is present.

### Bus / registry mismatch — ERROR / exit 1

`bus_derives_from_registry: true` is set in the registry and the `bus_graph` snapshot does not match the routing derived from `subscribes_to` fields.

The validator builds the expected bus graph: for each known event (from any agent's `publishes`, any non-wildcard agent's `subscribes_to`, plus `entry_events` and `terminal_events`), the expected subscribers are the agents that explicitly list that event in `subscribes_to`. Wildcard agents are not expanded into per-event entries — see **Wildcard convention** below.

Because entry events and terminal events are part of the known event vocabulary, include them in `bus_graph` when `bus_derives_from_registry: true`. Use an empty subscriber list for known events with no explicit subscribers, for example `"REPORT_DELIVERED": []`.

## Wildcard convention

An agent with `"subscribes_to": ["ALL"]` or `["*"]` is a wildcard observer. Rules:

- Wildcard agents are **never** flagged as orphan subscribers.
- A wildcard agent's presence suppresses all dead-end publish warnings (it covers every event).
- For bus graph comparison, wildcards are **not** expanded into individual event entries in the derived graph.
- If the runtime bus represents wildcards as a special top-level key (e.g. `"ALL": ["audit-logger"]`), include that key in `bus_graph`. The validator will then check it against the sorted list of wildcard agent IDs from the registry.
- If `bus_graph` has no `ALL`/`*` key, wildcard agents are ignored in per-event comparison — the snapshot is compared only on concrete event keys.

## Entry events

Events in `entry_events` are treated as externally published. Agents that subscribe to them are never flagged as orphan subscribers, because no registry agent needs to publish them.

When `bus_derives_from_registry: true`, entry events still belong in `bus_graph` so the bus snapshot covers every route the runtime can receive.

## Terminal events

Events in `terminal_events` may have no subscribers by design (external delivery, final output). No dead-end WARN is issued for them.

When `bus_derives_from_registry: true`, terminal events still belong in `bus_graph`, usually with an empty subscriber list.

## CI integration

### GitHub Actions

```yaml
- name: Validate registry
  run: python scripts/validate_registry.py registry.json
```

Exits 1 on orphan subscriptions or bus/registry mismatch — both fail the job. Dead-end WARN lines print but do not fail CI.

### Pre-commit hook

```bash
#!/bin/sh
python scripts/validate_registry.py registry.json
```

Place in `.git/hooks/pre-commit` and `chmod +x`.

### Claude Code session-start hook (`settings.json`)

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python scripts/validate_registry.py registry.json || echo '[registry] wiring errors — run python scripts/validate_registry.py registry.json'"
          }
        ]
      }
    ]
  }
}
```

## Example output

### All clear

```
OK     registry is valid
```

### Warnings only (dead-end publish)

```
WARN   dead-end publish: agent 'researcher' publishes 'RESEARCH_COMPLETE' but no agent subscribes to it
OK     no errors (warnings above)
```

### Errors

```
ERROR  orphan subscription: agent 'writer' subscribes to 'RESEARCH_COMPLETE' but no agent publishes it (and it is not an entry_event)
ERROR  bus/registry mismatch: event 'TASK_ASSIGNED': registry says ['researcher'], bus_graph says ['researcher', 'stale-agent']
```

## Flags

| Argument | Description |
|---|---|
| `registry` | Path to the registry JSON file (positional, required). |
| `--help` | Print usage, check descriptions, wildcard/entry/terminal conventions, and exit. |
