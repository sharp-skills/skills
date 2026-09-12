---
name: event-envelope
description: Define one wire contract for every event that crosses the bus — required correlation fields, a runtime tag, a mode tag — so a single control plane can re-enter a run identically no matter which runtime (local model, remote worker, browser, or plain code) emitted the event. Use this when agents run on more than one runtime and you need cross-runtime tracing and routing to stay consistent, when adding a new runtime keeps breaking event handling somewhere downstream, or when you want envelope validation that runs the same everywhere without a schema-library dependency.
license: Apache-2.0
---

# Event Envelope

The moment a multi-agent system spans more than one runtime — an agent in Claude Code, another on an OpenAI Codex worker, a step driven by an orchestrator like Hermes or LangGraph, a deterministic code handler, a browser driver — every one of them has to put its output on the same bus, and the control plane has to pick each event up and route it *without knowing or caring where it came from*. That only works if every event shares one shape. The envelope is that shape: a thin outer object with the fields the bus and the tracer need, wrapping an opaque agent-specific `payload` the bus never inspects.

In the source system this is the wire contract every runtime honors so the dispatcher re-enters identically wherever an agent ran. It is deliberately validated with stdlib only — no schema library — because a dependency one runtime has and another lacks would mean the same envelope is "valid" in one place and rejected in another.

## The envelope, minimally

Required on every event (the bus and tracer cannot function without them):

- **`trace_id`** — the correlation id carried across every local and remote step of one run. This is what makes cross-runtime tracing possible at all (see `observability-tracing`).
- **`agent`** — who emitted it (matches the registry short id).
- **`event`** — the event type / output status; this is what routing subscribes on (see `status-gates`).
- **`runtime`** — where it ran, from a closed enum.
- **`ts`** — ISO-8601 UTC emission time.

Optional, validated when present: **`pipeline_mode`** (closed enum, set once at phase 0), **`confidence_score`** (0–100 or null — decision agents score, infra agents don't), **`payload`** (opaque body, validated separately against the per-event schema, never by the bus).

`additionalProperties` stays **true**: the envelope is a floor, not a cage. Runtimes may add fields; they may never drop a required one or invent a runtime.

## The one bug this prevents: enum drift

The envelope's `runtime` enum and the dispatcher's routable runtime set are **the same fact written twice**. The failure mode is silent and delayed: you add a sixth runtime to the dispatcher, it routes fine, but the envelope schema still lists five — so events from the new runtime route correctly yet fail envelope validation (or the reverse). It only bites the runtime you added *last*, which is exactly the one you're not testing hard yet.

The fix is not vigilance, it's a check: treat one of the two as canonical (export the dispatcher's set to `runtimes.source`) and assert the schema enum equals it in CI. Now the pair can't drift without a red build. The same discipline is why `prompt-contracts` exists for prompt/schema enums — this is its runtime-vocabulary twin.

## Run vs read

| Resource | Action | Why |
|---|---|---|
| `scripts/envelope_check.py` | **RUN** | Two checks: `--runtimes-source` proves the schema's runtime enum equals the dispatcher's set (drift); `--events` validates a JSONL stream against required fields and enums. |
| `references/envelope-design.md` | **READ** | Field-by-field rationale, why stdlib validation, versioning the envelope, what belongs in the envelope vs the payload. |
| `examples/selftest.sh` | **RUN** | Proves the drift check and the wire check on shipped good/drifted/bad fixtures. |

```bash
python3 .../envelope_check.py --schema envelope.schema.json \
    --runtimes-source runtimes.source --events run.jsonl
```

## Common pitfalls

- **Two copies of the runtime enum with no check binding them.** The whole point; without the `--runtimes-source` assertion in CI, drift is a matter of time.
- **Putting agent-specific fields in the envelope.** If the bus doesn't route or trace on it, it belongs in `payload`. A bloated envelope couples every runtime to every agent's body.
- **Depending on a schema library for validation.** The rules must run identically under every runtime; a library one runtime lacks reintroduces the "valid here, invalid there" split the envelope exists to kill. Stdlib checks, or a validator vendored into every runtime.
- **`additionalProperties: false`.** Turns every additive change into a breaking one for the slowest-to-update runtime. Keep the envelope a floor.
- **Skipping `trace_id` on "internal" events.** An event without the correlation id is invisible to the tracer the moment it crosses a runtime — precisely when you most need it.
- **Booleans as scores.** `confidence_score: true` is `1` in a naive numeric check; the validator rejects bool explicitly.

## Verification checklist

- [ ] `sh examples/selftest.sh` passes (aligned enum + good stream → 0, drift → 1, malformed stream → 1, no-args → 2).
- [ ] The runtime enum in the schema is asserted equal to the dispatcher's set in CI, not by eye.
- [ ] Every required field is present on every emitted event across all runtimes (spot-check a real trace).
- [ ] Validation is stdlib-only or vendored identically into each runtime.
- [ ] `payload` is validated against its per-event schema separately, not by the envelope check.

## Related skills in this bundle

- `registry-ssot` — the registry is the source of truth for agents and events; the envelope is the source of truth for their *shape on the wire*.
- `status-gates` — routing subscribes on `event`; the gate checks that value where it becomes a routing decision. The envelope guarantees the field is there to check.
- `observability-tracing` — `trace_id` is what stitches one run's events into a timeline across runtimes.
- `prompt-contracts` — same anti-drift discipline, applied to prompt/schema enums instead of the runtime vocabulary.
- `mechanize-agents` — a `code` runtime handler emits the identical envelope an LLM agent did; that's what makes a flip invisible.
