---
name: registry-ssot
description: Drive a multi-agent event-driven system from one machine-readable registry and have the runtime derive routing from it instead of duplicating it. Use when agents or events are defined in more than one place (config, hardcoded graph, docs) and they have drifted; you see orphan subscriptions (an agent subscribes to an event no agent publishes); you hit dead-end publishes (an event emitted into the void); or your bus routing graph is out of sync with the registry.
license: Apache-2.0
---

# Registry as Single Source of Truth

Define every agent and its event wiring once in a machine-readable registry. Derive the runtime bus graph from that registry at load time instead of maintaining a second hardcoded routing map.

This skill exists because of a drift that shipped: a production multi-agent system kept its routing graph **twice** — once in the registry (documentation of record) and once hardcoded in the bus module (what actually ran). They diverged silently. Agents subscribed to events that were renamed on the publishing side; nothing errored, the subscriber simply never fired again, and the pipeline "worked" minus one agent. The fix that stuck was structural, not disciplinary: delete the hardcoded graph entirely and have the bus **build its routing from the registry at load time** — after that, drift is impossible rather than forbidden.

## Use this when

- Agents, events, or routing are defined in more than one place (config file, code, docs) — even if they haven't visibly drifted yet.
- An agent stopped reacting and nobody can say when or why (classic silent orphan subscription).
- Events are emitted that no one consumes, and you can't tell intentional terminals from lost wiring.
- You are adding an agent and have to remember *N* places to update — that memory is the defect.

Do not treat the registry as documentation. If humans read it but the runtime doesn't, it is a second copy of the truth by construction, and this skill's incident is already scheduled.

## The rule

> **The registry is the only place wiring exists. The runtime derives; humans edit one file; a validator guards the graph.**

Three structural properties make it hold:

1. **Derivation, not duplication.** The bus builds `event → subscribers` from the registry at load. There is nothing to keep in sync.
2. **Explicit terminals.** Events with intentionally no consumers are declared (`terminal_events`), so the validator can tell "designed endpoint" from "lost wiring" — otherwise every dead-end warning gets ignored and real losses hide among them.
3. **Named wildcards.** Observer agents that hear everything subscribe via an explicit wildcard token, not by enumerating (and forever chasing) the event list.

## Run vs read

| Resource | Action | Why |
|---|---|---|
| `scripts/validate_registry.py` | **RUN** | Black-box wiring check: orphan subscriptions and bus/registry mismatch = errors; dead-end publishes = warnings unless terminal. |
| `references/registry-schema.md` | **READ** | Registry shape: agents, publishes/subscribes, entry/terminal events, wildcard observers, bus graph snapshot. |
| `references/validation.md` | **READ** | CI, pre-commit, and session-start guardrail wiring. |
| `examples/selftest.sh` | **RUN** | Proves the validator on shipped good/bad registries (exits 0 / 1). |

```bash
python3 scripts/validate_registry.py registry.json
```

## Common pitfalls

- **Registry as prose.** A registry the runtime doesn't read is documentation wearing a config file's clothes; it will drift.
- **No terminal-event list.** Without it, dead-end warnings become noise, get ignored, and mask real lost wiring.
- **Validating only on "wiring changes".** Renames arrive disguised as refactors; run the validator in CI on every change to the registry or bus code.
- **Wildcard as a shortcut.** Making a normal agent a wildcard observer to "not miss anything" destroys the graph's meaning — reserve wildcards for genuine observers (bus monitors, watchdogs).
- **Extending the registry to silence a validator error.** Same inversion as any source-of-truth system: first decide whether the routing *should* change, then edit.

## Verification checklist

- [ ] `sh examples/selftest.sh` passes (good registry → 0, planted drift → 1).
- [ ] The runtime imports/derives its routing from the registry file (grep the bus code for a hardcoded event map — there must be none).
- [ ] `terminal_events` names every intentionally unconsumed event; the validator then reports zero dead-end warnings.
- [ ] Adding a test agent to the registry requires editing exactly one file.
- [ ] CI runs the validator on every registry/bus change.

## Related skills in this bundle

- `prompt-contracts` — the next layer up: keeps output schemas and prompts aligned to this registry's `publishes` vocabulary.
- `observability-tracing` — records what the derived routing actually did at runtime.
- `eval-harness` — scores the recorded runs against the structural contract.
