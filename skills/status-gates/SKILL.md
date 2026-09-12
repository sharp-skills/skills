---
name: status-gates
description: Validate every agent's emitted status at the dispatcher boundary of an event-routed multi-agent system, rejecting statuses the routing registry never publishes — with an explanation that teaches the model the allowed vocabulary and a retry cap that prevents infinite reject loops. Use this when an agent output "succeeds" but the pipeline silently stops, when a model invents status values under pressure, when retries loop forever on the same rejection, or as the runtime companion to static prompt-contract checking.
license: Apache-2.0
---

# Status Gates at the Routing Boundary

In an event-routed pipeline the agent's output `status` is consumed as a routing event: it decides who runs next. A status the registry doesn't know doesn't crash anything — it simply routes nowhere, and the pipeline stops with every component reporting success. The gate closes exactly that hole: at the moment an output becomes a routing decision, check the status against the agent's registry vocabulary, and reject invalid ones **loudly, with the allowed list in the rejection**.

Static contract checking (see `prompt-contracts`) guarantees the files *agree*; this gate handles the case files can't cover — the model disobeying an agreed contract at runtime. You need both: they fail differently.

## Use this when

- A pipeline halts mid-run with no error anywhere — the classic silent un-route.
- Models under pressure emit plausible-but-unregistered statuses (`SUCCESS`, `DONE`, `OK` are the usual inventions).
- A rejected output is retried forever with the same wrong status.
- You are enforcing contracts that were previously advisory (warn → enforce flip) and need the runtime side in place first.

## Gate rules (each traceable to an incident)

1. **The allowed set is derived, never listed locally.** Allowed = the agent's registry `publishes` ∪ skip forms (`*_SKIPPED`) ∪ the shared failure terminal (`PIPELINE_FAILED`). A locally maintained copy of this set is contract drift waiting to happen. The gate reads the *same* registry the bus derives from — either shape works (agents as a dict, or the canonical `registry-ssot` list of `{id, publishes}`) — so the gate and the router share one source of truth, not a gate-private copy.
2. **Reject messages teach.** The rejection an agent receives contains the allowed vocabulary: "status `SUCCESS` never routes; this agent may emit `BA_COMPLETE`, `BA_BLOCKED`, `PIPELINE_FAILED`". A bare rejection produces the same wrong answer again; a teaching rejection converges in one retry. In production this single change turned a dead first run into a self-correcting one.
3. **Cap the reject loop.** Reject + retry without a counter is an infinite loop wearing a safety vest. After N rejections (2–3), stop retrying and escalate: emit the shared failure event with the rejection history attached.
4. **Observers are exempt by name.** Agents whose `status` reports a delivery/ack outcome rather than a bus event (event-bus monitors, watchdogs) are outside the gate's premise. The exemption is a named list — implicit exemptions are unguarded surface.
5. **Unknown agents fail open.** If the agent isn't in the registry, that's a registration problem, not a status problem; a different check owns it (see `registry-ssot`). Gates that grab jurisdiction beyond their premise block legitimate work and get disabled.

## Run vs read

| Resource | Action | Why |
|---|---|---|
| `scripts/status_gate.py` | **RUN** | The gate as a library + CLI: check one emitted status against a registry; exit 0 = routes, 2 = would never route. |
| `references/gate-design.md` | **READ** | Where to place the gate, message design, retry-cap escalation, warn→enforce rollout order. |
| `examples/selftest.sh` | **RUN** | Proves allow/reject/exempt/fail-open paths on a shipped registry. |

```bash
python3 .../status_gate.py --registry registry.json --agent business_analyst --status BA_COMPLETE
python3 .../status_gate.py --registry registry.json --agent business_analyst --status SUCCESS   # exit 2 + teaching message
python3 .../status_gate.py --registry registry.json --config gate-config.json --agent event_bus --status DELIVERED  # exempt observer
```

The config file shares its vocabulary with `prompt-contracts` (`extra_allowed`, `allowed_suffixes`, `exempt`, registry paths) — one contract, two enforcement points.

## Rollout order (warn → enforce)

1. Run `prompt-contracts` static check and fix all drift first. Enforcing a gate against prompts that teach forbidden statuses guarantees a reject storm.
2. Wire the gate in **warn mode**: log would-be rejections for a few runs; each warning is either model disobedience (gate is right) or contract drift the static check missed (fix the files).
3. Flip to enforce with the retry cap in place.
4. Delete any temporary status allowances added during rollout — a relaxed gate that outlives its incident is the next incident.

## Common pitfalls

- **Enforcing before aligning.** The gate amplifies whatever the prompts teach; align first (see rollout order).
- **Bare rejections.** Without the allowed list in the message, the model retries the same invention; see rule 2.
- **No retry cap.** The first production gate died exactly this way — guaranteed reject + automatic retry = a loop that burns quota until a human notices.
- **Gate-side vocabulary copies.** Deriving from the registry at load is the whole point; a hardcoded allowed-set drifts like any second copy of truth.
- **Exempting by pattern.** "Skip anything that looks like an observer" is fail-open jurisdiction creep; exempt by explicit name.

## Verification checklist

- [ ] `sh examples/selftest.sh` passes (allow / reject / skip-form / shared terminal / exempt observer / unknown agent).
- [ ] A rejection message contains the agent's full allowed vocabulary.
- [ ] The dispatcher counts rejections per agent per run and escalates after the cap.
- [ ] The gate reads `publishes` from the same registry file the bus derives routing from.
- [ ] Warn-mode logs were reviewed before the enforce flip.

## Related skills in this bundle

- `prompt-contracts` — the static half of the same contract; run its checker in CI, this gate at runtime.
- `registry-ssot` — the registry this gate derives every allowed set from.
- `observability-tracing` — log gate rejections as trace events; a reject storm should be visible on the timeline, not only in stderr.
- `eval-harness` — rejected statuses surface as blocking flags when traces carry gate outcomes in `meta`.
