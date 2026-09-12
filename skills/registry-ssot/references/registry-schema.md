# Registry Schema

The registry is a single JSON file that is the authoritative source of truth for all agents and their event wiring. The runtime bus, documentation, and tooling derive from it — they do not maintain their own copies.

## Top-level fields

| Field | Type | Required | Description |
|---|---|---|---|
| `agents` | array | yes | Array of agent descriptor objects (see below). |
| `terminal_events` | string[] | no | Events that end a pipeline by design and need no subscriber. Dead-end publish warnings are suppressed for these. |
| `entry_events` | string[] | no | Events injected from outside the system (user input, external triggers). They need no publisher in the registry. |
| `bus_derives_from_registry` | boolean | no | When `true`, the validator checks that `bus_graph` matches routing derived from the registry. |
| `bus_graph` | object | no | Snapshot of the runtime's actual routing table. Used only for comparison when `bus_derives_from_registry` is `true`. |

## Agent descriptor fields

Each object in `agents[]` describes one agent:

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | yes | Unique, stable agent identifier. Use a consistent convention (e.g. lowercase-kebab). |
| `level` | integer | yes | Hierarchy level. Conventionally: 0 = infrastructure/observer, 1 = orchestrator, 2 = worker. |
| `prompt_file` | string | yes | Path to the agent's system prompt, relative to the project root. |
| `subscribes_to` | string[] | yes | Events this agent reacts to. Use `["ALL"]` or `["*"]` for wildcard (observer/logger). |
| `publishes` | string[] | yes | Events this agent emits. Use `[]` if the agent produces no events. |
| `contract` | object | no | Operational constraints for this agent (see below). |

### `contract` object

| Field | Type | Description |
|---|---|---|
| `active_modes` | string[] | Pipeline modes in which this agent is active (e.g. `["standard", "fast"]`). Agents not active in the current mode are excluded from routing. |

## Wildcard subscribers

Setting `"subscribes_to": ["ALL"]` (or `["*"]`) makes an agent a wildcard subscriber — it receives every event on the bus. Wildcard subscribers are:

- **Never** flagged as orphan subscribers, even if specific events are not published.
- Counted as covering all published events for dead-end publish checks (no WARN if wildcards exist).
- Typically used for loggers, monitors, and audit agents.

## Terminal events

Events in `terminal_events` are explicitly classified as pipeline end-states. They:

- May have no subscribers by design (external delivery, user-facing output, etc.).
- Do not trigger a dead-end publish warning.
- Should still be published by at least one agent in the registry.

## Entry events

Events in `entry_events` are injected from outside the system (e.g. user submits a task, external webhook fires). They:

- Do not need a publisher inside the registry.
- Do not trigger an orphan subscription warning when agents subscribe to them.

## `bus_graph` field

When `bus_derives_from_registry: true`, include a `bus_graph` snapshot for comparison. The validator checks that the bus graph matches the routing implied by all `subscribes_to[]` fields.

Format: `{ "EVENT_NAME": ["agent-id-a", "agent-id-b"], ... }`

## Annotated example

```json
{
  "bus_derives_from_registry": true,
  "entry_events": ["TASK_SUBMITTED"],
  "terminal_events": ["TASK_REJECTED", "REPORT_DELIVERED"],
  "agents": [
    {
      "id": "orchestrator",
      "level": 1,
      "prompt_file": "prompts/orchestrator.md",
      "subscribes_to": ["TASK_SUBMITTED"],
      "publishes": ["TASK_ASSIGNED", "TASK_REJECTED"],
      "contract": {
        "active_modes": ["standard", "fast"]
      }
    },
    {
      "id": "researcher",
      "level": 2,
      "prompt_file": "prompts/researcher.md",
      "subscribes_to": ["TASK_ASSIGNED"],
      "publishes": ["RESEARCH_COMPLETE"],
      "contract": {
        "active_modes": ["standard", "fast"]
      }
    },
    {
      "id": "writer",
      "level": 2,
      "prompt_file": "prompts/writer.md",
      "subscribes_to": ["RESEARCH_COMPLETE"],
      "publishes": ["REPORT_DELIVERED"],
      "contract": {
        "active_modes": ["standard"]
      }
    },
    {
      "id": "audit-logger",
      "level": 0,
      "prompt_file": "prompts/audit-logger.md",
      "subscribes_to": ["ALL"],
      "publishes": [],
      "contract": {
        "active_modes": ["standard", "fast"]
      }
    }
  ],
  "bus_graph": {
    "TASK_SUBMITTED": ["orchestrator"],
    "TASK_ASSIGNED": ["researcher"],
    "RESEARCH_COMPLETE": ["writer"],
    "TASK_REJECTED": [],
    "REPORT_DELIVERED": []
  }
}
```

### What this example encodes

- `orchestrator` reacts to external input (`TASK_SUBMITTED` is an entry event) and either assigns or rejects the task.
- `researcher` handles assigned tasks and emits results.
- `writer` turns research into a deliverable report.
- `audit-logger` observes every event without filtering — a wildcard subscriber.
- `TASK_REJECTED` and `REPORT_DELIVERED` are terminal events: they have no downstream subscribers by design.
- `bus_graph` captures the runtime's actual routing; the validator checks it matches the registry.
