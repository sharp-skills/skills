# multi-agent-engineering

Twenty-five procedural skills for building and operating production
multi-agent systems. Every skill is derived from operating a real
event-driven multi-agent pipeline (30+ agents), not compiled from articles:
the failure modes cite production incidents, the scripts are the generalized
form of guards that run in that system's CI today, and each skill ships
fixtures that prove its claims offline (`sh examples/selftest.sh` — stdlib
Python only, no network, no credentials).

The skills are grouped by the failure class they guard. Near-neighbours are
kept together with a note on **why they are disjoint** — this bundle catches
different failures, it does not restate one idea many ways.

## How the core spine stacks

```
registry-ssot          the wiring truth: one machine-read registry,
      │                routing derived, never duplicated
      ▼
prompt-contracts       the static guard: schemas and prompts may only
      │                narrow the registry, never extend it
      ▼
status-gates           the runtime guard: emitted statuses checked at the
      │                routing boundary, rejections that teach
      ▼
governance-hooks       the harness guard: no-touch zones, secrets, drift —
      │                enforced by hooks, not by asking the model nicely
      ▼
task-triage            the economizer: the smallest crew that can deliver,
      │                with an anti-stall reachability proof
      ▼
observability-tracing  the flight recorder: one JSONL trace per run
      │
      ▼
eval-harness           the measure: deterministic structural + grounding
                       score, regression baselines, LLM-as-judge seam
```

Adopt roughly in that order: establish the source of truth, guard the
contract statically and at runtime, protect the system from its own agents,
economize the crew, record what happens, then measure it. Each skill also
stands alone.

## See it run together

The skills compose into one system — not a pile of singles. [`demo/`](demo/)
wires five of them through **one shared registry and one trace** in a single
runnable pipeline (stdlib, offline):

```bash
sh demo/demo.sh
```

Routing is derived from the registry (`registry-ssot`), every emitted status is
gated at the routing boundary (`status-gates`), every step is recorded
(`observability-tracing`), then the same trace is scored (`eval-harness`) and
budget-checked (`cost-budgeting`). A final failure path shows an unroutable
status rejected with a teaching message instead of a silent stall. See
[`demo/README.md`](demo/README.md).

[`demo-security/`](demo-security/) is the second composition, over a threat
rather than a pipeline: one attack — an injection in a fetched page that tries to
exfiltrate the repo — is driven through all five security checkers as ordered
echelons. It runs twice, hardened and breached, and each wall reddens for its own
reason:

```bash
sh demo-security/demo-security.sh
```

To check the whole bundle at once — every skill's self-test plus both demos:

```bash
sh bundle_check.sh
```

## Core skills

### Wiring & contracts — keep the routing honest
Four layers, four different drifts. The registry is the source of truth;
contracts check the files *agree* before a run (and keep each prompt pinned,
changelogged, and rollback-ready — the prompt you have *and* the prompt you
change); status-gates catch the model *disobeying* at runtime; the envelope is
the cross-runtime wire shape. None substitutes for another.

| Skill | One line | Verify |
|---|---|---|
| [registry-ssot](../../skills/registry-ssot/SKILL.md) | Define agents/events once; derive the bus graph; validate orphans, dead-ends, drift | `sh registry-ssot/examples/selftest.sh` |
| [prompt-contracts](../../skills/prompt-contracts/SKILL.md) | Registry ⊇ schema enums ⊇ prompt examples, checked statically; plus prompt versioning — content-hash pins, changelogs, rollback | `sh prompt-contracts/examples/selftest.sh` |
| [status-gates](../../skills/status-gates/SKILL.md) | Emitted status validated where it becomes a routing event; teaching rejections, capped retries | `sh status-gates/examples/selftest.sh` |
| [event-envelope](../../skills/event-envelope/SKILL.md) | One wire shape for every event; the runtime enum stays equal to the dispatcher's set — no schema library | `sh event-envelope/examples/selftest.sh` |

### Security & trust — defense in depth
Disjoint failure classes: where capability lives, whose word an agent believes,
untrusted text, tool execution, persistent memory, harness-level enforcement, and
how much authority an agent holds in the first place. An attack stopped by one
wall walks through the others.

| Skill | One line | Verify |
|---|---|---|
| [agent-isolation](../../skills/agent-isolation/SKILL.md) | Never let one session hold sensitive access + untrusted input + an exfil channel (the lethal trifecta) | `sh agent-isolation/examples/selftest.sh` |
| [multi-agent-trust](../../skills/multi-agent-trust/SKILL.md) | Trust a message by the channel it arrived on, not the source it claims; privileged asks need a trusted tier | `sh multi-agent-trust/examples/selftest.sh` |
| [prompt-injection-guard](../../skills/prompt-injection-guard/SKILL.md) | Delimit untrusted content as data and flag injection signatures — the structural wall behind isolation | `sh prompt-injection-guard/examples/selftest.sh` |
| [tool-call-validator](../../skills/tool-call-validator/SKILL.md) | Pre-flight every tool call: known tool, complete args, destructive approved, no redundant repeats | `sh tool-call-validator/examples/selftest.sh` |
| [agent-memory-hygiene](../../skills/agent-memory-hygiene/SKILL.md) | Keep memory trustworthy: provenance, freshness, no secrets, untrusted content never stored as fact | `sh agent-memory-hygiene/examples/selftest.sh` |
| [governance-hooks](../../skills/governance-hooks/SKILL.md) | No-touch zones, secret access, config drift — enforced in the harness via hooks, not prompts | `sh governance-hooks/examples/selftest.sh` |
| [earned-autonomy](../../skills/earned-autonomy/SKILL.md) | Authority is earned on a four-rung ladder and paid for by clean human verdicts, not configured once at integration time; no agent grants itself | `sh earned-autonomy/examples/selftest.sh` |

### Review & verification — three reviews that miss different things
Completeness, quality, and robustness are separate blind spots. An artifact can
pass a quality critic and a completeness verifier and still fold to "ignore your
instructions."

| Skill | One line | Verify |
|---|---|---|
| [cross-model-verification](../../skills/cross-model-verification/SKILL.md) | A different model family verifies hand-off completeness; deterministic floor; fails soft | `sh cross-model-verification/examples/selftest.sh` |
| [two-layer-critic](../../skills/two-layer-critic/SKILL.md) | Cheap review always, premium reserved for high stakes; ≤3 structured findings, pass/fail | `sh two-layer-critic/examples/selftest.sh` |
| [adversarial-agent-review](../../skills/adversarial-agent-review/SKILL.md) | Gate on a red-team probe suite: coverage, every probe answered, no attack succeeded, critical fails block | `sh adversarial-agent-review/examples/selftest.sh` |

### Economics & scope — bound the spend three ways it blows up
Cost spikes through token volume, delegation topology, or over-broad crews. Each
cap catches what the others can't see.

| Skill | One line | Verify |
|---|---|---|
| [cost-budgeting](../../skills/cost-budgeting/SKILL.md) | Per-agent/per-run token budgets checked over recorded traces; decompose over extend | `sh cost-budgeting/examples/selftest.sh` |
| [delegation-guards](../../skills/delegation-guards/SKILL.md) | Bound spawn depth, fan-out, and total agents; detect delegation cycles — no runaway swarm | `sh delegation-guards/examples/selftest.sh` |
| [task-triage](../../skills/task-triage/SKILL.md) | LLM proposes the crew, rules guard it, reachability check prevents silent stalls | `sh task-triage/examples/selftest.sh` |

### Runtime & lifecycle — operating the running system
Retire LLMs where code is enough, fit long runs into the context window, survive
being interrupted, accrue experience across sessions, safely consume another
agent's output, and keep the model underneath from moving without you noticing.

| Skill | One line | Verify |
|---|---|---|
| [mechanize-agents](../../skills/mechanize-agents/SKILL.md) | Flip rule-defined agents from LLM to code — same events out, dry-run first, hybrid defer for ambiguity | `sh mechanize-agents/examples/selftest.sh` |
| [context-compression](../../skills/context-compression/SKILL.md) | Configure native compaction, don't build it; the summarizer's window must be ≥ the main model's | `sh context-compression/examples/selftest.sh` |
| [experience-loop](../../skills/experience-loop/SKILL.md) | EMA confidence + structured learnings, captured at completion, distilled into prompt fixes | `sh experience-loop/examples/selftest.sh` |
| [llm-output-parsing](../../skills/llm-output-parsing/SKILL.md) | Get a typed value from prose you can't control OR "mostly-JSON" — flag conflicts, safe-repair, validate, never guess | `sh llm-output-parsing/examples/selftest.sh` |
| [durable-sessions](../../skills/durable-sessions/SKILL.md) | Survive a crash mid-session: replay recorded outcomes instead of re-running them, key side effects, bound retries, scope caches | `sh durable-sessions/examples/selftest.sh` |
| [model-version-pinning](../../skills/model-version-pinning/SKILL.md) | Pin models to exact artifacts, not floating aliases; shadow-run each release against a frozen probe set and compare trajectories, not scores | `sh model-version-pinning/examples/selftest.sh` |

## Infrastructure

Foundational rather than novel — the measurement substrate the rest of the
bundle records and scores on. Included for a complete stack, not for a clever
insight; adopt them for the baseline they give the sharper skills.

| Skill | One line | Verify |
|---|---|---|
| [observability-tracing](../../skills/observability-tracing/SKILL.md) | Per-trace JSONL logging that never breaks the pipeline + timeline viewer | `sh observability-tracing/examples/selftest.sh` |
| [eval-harness](../../skills/eval-harness/SKILL.md) | 0–100 structural rubric over traces + grounding audit (claims must cite a resolving source); regression baselines; judge seam separate | `sh eval-harness/examples/selftest.sh` |

## Form

Every skill follows the same contract: frontmatter with trigger-rich
`description` (Agent Skills spec) · a body under ~150 lines · a **Run vs
read** table · real **failure modes / pitfalls** · a **verification
checklist** · `scripts/` that are stdlib-only and CI-friendly (exit 0 =
holds, 1 = violations, 2 = the check itself couldn't run honestly) ·
`references/` loaded on demand · `examples/` with a self-test.

License: Apache-2.0.
