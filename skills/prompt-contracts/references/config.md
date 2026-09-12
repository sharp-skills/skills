# contract-config.json — shape and rationale

The checker is project-agnostic: everything project-specific lives in one JSON
config. Wiring is **explicit by design** — see F-3 in the failure catalog for
why derived/implicit mappings are forbidden.

## Full example

```json
{
  "root": "..",
  "registry": {
    "file": "config/agent_registry.json",
    "agents_path": "agents",
    "publishes_key": "publishes"
  },
  "extra_allowed": ["PIPELINE_FAILED"],
  "allowed_suffixes": ["_SKIPPED"],
  "exempt": ["EVENT-BUS", "WATCHDOG"],
  "agents": {
    "BA": {
      "registry_id": "business_analyst",
      "schema": "config/schemas/ba_output.json",
      "prompts": ["config/prompts/*Business_Analyst*.md"]
    },
    "CTO": {
      "schema": "config/schemas/cto_output.json",
      "prompts": ["config/prompts/*CTO*.md"]
    }
  }
}
```

## Fields

| Field | Required | Meaning |
|---|---|---|
| `root` | no | Base directory for all relative paths, resolved relative to the config file. Default `.`. |
| `registry.file` | yes | The routing registry — the single source of truth for who may publish what. |
| `registry.agents_path` | no | Dotted path to the agent map inside the registry JSON (`""` = the document itself is the map). |
| `registry.publishes_key` | no | Key holding the agent's publishable events. Default `publishes`. |
| `extra_allowed` | no | Statuses every agent may emit besides its publishes — typically the one shared pipeline-failure event. Keep this list short; it is a global widening. |
| `allowed_suffixes` | no | Suffix forms allowed for conditional agents, e.g. `_SKIPPED` for "I was conditionally not needed". |
| `exempt` | no | **Named** observer/ack agents whose `status` is a delivery outcome, not a routing event. Anything not named here is checked. |
| `agents` | yes | Explicit map: config agent id → wiring. |
| `agents.<id>.registry_id` | no | Registry key if it differs from the config id. Aliases are declared, never derived. |
| `agents.<id>.schema` | yes* | Path or list of paths/globs to the agent's output schema(s). |
| `agents.<id>.prompts` | yes* | Path(s)/glob(s) to the agent's prompt files. |

\* An agent may have only one of the two (schema-only or prompt-only checking),
but a glob that matches **nothing** is an error, not a skip.

## Interpreting results

- **exit 0** — contract holds. Safe to flip soft gates to enforce.
- **exit 1** — violations listed per agent. Follow the repair procedure in
  SKILL.md: registry wins; schemas narrow; prompts (especially worked
  examples) follow; shims die.
- **exit 2** — the check itself couldn't run honestly: missing files, empty
  globs, unresolvable registry ids, invalid JSON. Never downgrade these to
  warnings — a guard that skips what it can't resolve is fail-open (F-3).

## CI wiring

Run on every change to prompts, schemas, or the registry:

```yaml
- name: Prompt contract check
  run: python3 skills/prompt-contracts/scripts/contract_check.py --config contract-config.json
```

Pair it with a runtime status gate (dispatcher rejects unregistered statuses).
The static check keeps the layers agreeing; the runtime gate catches the model
disobeying an agreed contract. You need both — they fail differently.
