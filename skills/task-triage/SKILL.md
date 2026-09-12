---
name: task-triage
description: Route each task to the smallest crew of agents that can deliver it, instead of firing the whole multi-agent graph on every request — an LLM proposes the crew, deterministic rules guard it, and a reachability check proves the scoped pipeline can still finish. Use this when every small task runs all N agents and burns tokens/time, when a "write a blog post" request wakes the engineering pipeline, when compliance agents get skipped on tasks that legally need them, or when a scoped run stalls before reaching a terminal event.
license: Apache-2.0
---

# Task Triage / Crew Scoping

A multi-agent system tuned for its hardest task overcharges every easier one: a request for a small utility function does not need market research, financial gating, UX design, and growth analytics. Triage decides **which agents a task actually needs** and hands the dispatcher a *scope* — the set of agents it may offer. Measured effect in the source system: a routine task dropped from 33 pipeline steps to 16 with an identical deliverable.

The danger is equally real in the other direction: an over-eager triage that drops a compliance agent from a payments task, or breaks the event chain so the scoped pipeline stalls mid-run. So the design is **hybrid, with the LLM proposing and rules disposing**.

## Use this when

- Small tasks pay the full-crew cost in tokens, latency, and review noise.
- Task classes are recognizably different (content vs feature vs infra) but all take the same route.
- You tried LLM-only routing and it under-scoped something that mattered (the classic: legal skipped on a billing task).
- A scoped run once stalled silently — an agent's trigger event was published by someone outside the scope.

## The hybrid rule

> **A cheap LLM classifies; deterministic rules override; the spine is non-negotiable; unknown means everyone.**

1. **Mandatory spine.** Each route keeps a core chain whose links publish each other's triggers all the way to a terminal event. Cutting a spine agent doesn't degrade the pipeline — it stalls it (validated empirically: every stall in testing was a missing spine agent).
2. **Templates over free choice.** The classifier picks from named crew templates (task class → optional groups), not from 2^N agent subsets. Bounded choices = bounded failure modes.
3. **Force rules trump the LLM.** Keyword guards add compliance-critical groups regardless of the classification: payments/PII vocabulary forces the legal group in even if the model said "simple feature". Under-scoping compliance is the one mistake this design refuses to allow the LLM.
4. **Fail soft to rules.** If the classifier call fails or returns junk, keyword routing takes over. Triage must never become a pipeline dependency.
5. **Unknown → full crew.** The default template is everyone. Scoping is an optimization; safety is the default.
6. **Scope, not surgery.** The output is a *filter the dispatcher applies* (`scope=None` = legacy full-graph behavior). The registry and routing graph are untouched — triage is removable in one line.

## Run vs read

| Resource | Action | Why |
|---|---|---|
| `scripts/triage.py` | **RUN** | Classify a goal → scope JSON; `--check-registry` proves the scope can reach a terminal event (anti-stall). |
| `references/design.md` | **READ** | Template/force-rule design, short routes, the stall class, external-classifier wiring, rollout. |
| `examples/selftest.sh` | **RUN** | Proves routing, force rules, full-crew default, and stall detection on shipped fixtures. |

```bash
# classify a goal (rules-only; add an external classifier later)
python3 .../triage.py "write a blog post about our Q3 launch" --config triage-config.json

# with anti-stall proof against the routing registry
python3 .../triage.py "add a billing endpoint" --config triage-config.json --check-registry registry.json
```

Output is JSON: the scope (agent ids), the chosen template, which groups were forced in by rules, and the classification source (`llm` or `rules`).

## Common pitfalls

- **Letting the LLM own the decision.** The classifier is a suggestion engine; rules own compliance and the spine. Reversing that ratio re-creates the under-scoping incident.
- **Scoping without a reachability check.** A scope that severs the event chain fails as a silent stall, the worst failure class. Run `--check-registry` in CI for every template.
- **Defaulting to the smallest crew.** Unknown tasks get the full crew; the burden of proof is on scoping down, never up.
- **Encoding routes in code.** Templates, groups, force rules, and keywords are config — tuning triage must be an edit + review, not a deploy.
- **Monolingual keyword rules.** If goals arrive in more than one language, force rules must cover all of them — a Russian-language payments task must still force legal in.

## Verification checklist

- [ ] `sh examples/selftest.sh` passes (content route, forced legal, full-crew default, stall detection).
- [ ] Every template passes `--check-registry` (a terminal event is reachable inside the scope).
- [ ] A goal containing payments/PII vocabulary forces the compliance group regardless of classifier output.
- [ ] Killing the classifier (no external command) still routes via keywords.
- [ ] Disabling triage (`scope=None`) restores full-graph behavior with no other change.

## Related skills in this bundle

- `registry-ssot` — the registry is what makes the reachability proof possible; triage reads it, never edits it.
- `status-gates` — scoped runs still pass every status through the gate; triage narrows *who runs*, not *what they may say*.
- `observability-tracing` — compare traces before/after scoping; the 33→16 measurement is exactly a trace diff.
- `eval-harness` — baseline the scoped pipeline to prove the deliverable didn't degrade with the crew.
