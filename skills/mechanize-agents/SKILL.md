---
name: mechanize-agents
description: >-
  Replace LLM agents with deterministic code where the work is rule-defined — git operations, session bookkeeping, threshold verdicts — keeping the same registry events so the rest of the pipeline can't tell the difference. Use this when an agent's job is a pure input→output mapping and hallucination adds risk without adding value, when LLM cost/latency on mechanical steps dominates a run, or when you need a hybrid: code for the clear cases, deferring to the LLM only on ambiguity.
license: Apache-2.0
---

# Mechanize Deterministic Agents

Some agents in a multi-agent pipeline don't think — they follow rules: build a git command from a payload, save and load session state, compare a number to a threshold. Running a language model on rule-defined work buys you nothing and sells you three risks: hallucinated commands, nondeterministic outputs on identical inputs, and per-call cost/latency on the hottest path. This skill is the discipline for flipping such agents to plain code — **without the rest of the system noticing**.

In the source system three agents were mechanized this way (git automation, session manager, and a financial gate); the pipeline's routing, schemas, and downstream consumers required zero changes, because the flip preserved the one thing that matters: the events.

## Use this when

- An agent's prompt is essentially a specification: "given payload X, do exactly Y".
- The same input should always produce the same output, and today it doesn't.
- A hot mechanical step (state save/load, command building) pays LLM latency on every run.
- A verdict is a formula (ROI ≥ threshold) but edge cases still need judgment — the hybrid case.

Do not mechanize judgment. If reasonable experts could disagree on the output, code will encode one opinion and silently apply it forever. The test: write the spec; if writing it *completely* is impossible, the agent stays an LLM (or goes hybrid).

## The three rules of a safe flip

1. **Same events out.** The code handler returns the exact canonical registry events the LLM version published. The registry entry gains `runtime: "code"`; nothing else in the system changes. This makes the flip reversible in one line — and testable by diffing traces.
2. **Dry-run by default, execution by explicit consent.** A mechanized handler with side effects (git push, PR merge) builds the command and returns the event *without executing* until an explicit environment flag enables it. Merging the code changes nothing until someone deliberately flips the switch — deployment and go-live are separate decisions.
3. **LLM-authored payloads are untrusted input.** The payload your handler receives was written by a model. Validate it like user input from the internet: reject values that look like command flags, allowlist repository/path formats, and confine filesystem operations to declared directories. In the source system this is exactly how a rollback handler is prevented from running git commands in an arbitrary checkout.

## The hybrid pattern (code first, LLM on ambiguity)

For verdict-type agents, mechanize the clear cases and **defer** the rest:

- The code path computes the verdict when inputs are complete and consistent.
- On missing inputs, contradictions, or claims that would change the verdict, it returns a *defer status* (e.g. `ANALYST_REQUIRED`) with the reason attached.
- **The defer status is NOT a bus event.** The orchestrator sees it and re-invokes the LLM analyst with the defer reason as context; the registry's event vocabulary stays untouched. Routing the defer through the bus would double the event surface for what is an internal hand-off.

This keeps the cheap deterministic path for ~90% of runs while ambiguity still gets judgment — and the defer reasons accumulate into a spec for mechanizing the next slice.

## Run vs read

| Resource | Action | Why |
|---|---|---|
| `scripts/runtime_audit.py` | **RUN** | Audits the registry ↔ handler manifest: every code agent has a handler, handler events ⊆ registry publishes, hybrids declare a defer status that is not a bus event. |
| `references/selection-and-golive.md` | **READ** | What to mechanize (and what never), payload validation patterns, the dry-run → go-live runbook. |
| `examples/selftest.sh` | **RUN** | Proves the audit on shipped good/broken manifests. |

```bash
python3 .../runtime_audit.py --registry registry.json --manifest handlers.json
```

## Common pitfalls

- **Mechanizing judgment because the prompt looks simple.** A short prompt can hide taste; the spec test (above) decides, not prompt length.
- **New events for the code path.** If the flip changes the event vocabulary, every consumer changes with it — you've rewritten the pipeline, not mechanized an agent.
- **Trusting the payload.** The model upstream *will* eventually produce a payload with a `--force` where a branch name belongs. Validate shapes, not intentions.
- **Go-live bundled with merge.** Side-effectful handlers must land dark (dry-run) and be enabled by a separate, reviewed decision.
- **Routing defer statuses through the bus.** Defer is an internal hand-off; making it an event doubles vocabulary and invites contract drift (see `prompt-contracts`).
- **Deleting the LLM prompt after the flip.** Keep it — it is the fallback (`runtime` flip-back) and the documentation of intent.

## Verification checklist

- [ ] `sh examples/selftest.sh` passes (complete manifest → 0, missing handler / unregistered event / defer-as-bus-event → 1).
- [ ] Trace diff before/after the flip shows identical event sequences on identical inputs (see `observability-tracing`).
- [ ] Side-effectful handlers do nothing without the explicit execute flag.
- [ ] Payload validation rejects flag-shaped values and out-of-allowlist repos/paths.
- [ ] The registry note records when and why the agent was mechanized.

## Related skills in this bundle

- `registry-ssot` — `runtime` lives in the registry entry; the flip is a registry change, reviewed like any wiring change.
- `status-gates` — code handlers pass the same gate as LLM agents; a handler emitting an unregistered event is caught at the same boundary.
- `prompt-contracts` — the defer-status rule ("not a bus event") is enforced by keeping it out of `publishes`; the audit script checks exactly that.
- `task-triage` — mechanized agents make the spine cheaper, which changes the economics triage optimizes.
